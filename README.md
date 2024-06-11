# Gaming Analytics with Confluent, StarTree and AWS
Create a data streaming pipeline for a video game simulation. Experience real time data processing for better and faster decision-making. In this workshop, you will run a local client that will simulate player movements. Player coordinates as well as player collisions (labelled as interactions) are sent to Confluent Cloud for processing. You will create real time transformations to identify cheaters, track hot spots on the map, etc.

# Requirements
1. Confluent Cloud account
1. StarTree Cloud account
1. Workshop Time: ~ 45 min


# Setting Up Confluent Cloud
1. Log into [confluent.cloud](https://confluent.cloud)
2. Create a new environment
3. Create a new Standard cluster. Select us-east-2 for the region.
4. Create API Keys (also known as Kafka API Keys within Confluent Cloud). These will allow the local client to interact (sink and source data) with Confluent Cloud.
6. Create a new topic called `interactions`. Leave the partitions set to 6. This will be one of the places where data from the local client will land.
7. Create a new topic called `player-position`. Leave the partitions set to 6. This will be one of the places where data from the local client will land.

# Setting Up StarTree Cloud
1. Todo

# Run the Local Client
## Setup
1. Rename the file named `example-client.properties` to `client.properties`. This file will be used by the local client to push game data into Confluent Cloud.
1. Fill out the the `client.properties` file for the following fields:
    - bootstrap.servers: to find this value, navigate to your cluster in Confluent Cloud. Find the cluster settings tab and find the `Bootstrap server` label.
    - sasl.username: This is the Key of your Kafka API Keys you created earlier.
    - sasl.password: This is the Secret of your Kafka API keys you created earlier.

1. Run the following command: `python3 run-game-simulation.py`

## View the Incoming Messages
1. Log into Confluent Cloud and navigate to your cluster for this workshop
1. Navigate to the Topics section and click `player-position`
1. Click the `Messages` tab. If you have everything properly configured, you will see messages flow into the topic
![](assets/topic-throughput-check.png)
1. You can choose to do the same with the `interactions` topics
1. \[Optional\] Feel free to pause the python script from above while you work on the next section.

# Real Time Transformation
With data flowing from the local game client into the Confluent Cloud, we will now perform real time transformations on the data as it comes in. Such transformations include joining data from multiple sources, filtering data by value, or routing data based on conditions. By doing so, we leverage the full potential of the once-siloed data to answer questions such as "which players are cheating?" or "where on the map are most players engaging?"

## Query 1 - Enriched Interactions
This sql joins the `interactions` table/topic and the `player_position` table/toic. The output provides interaction records with coordinates that identify where the engagement occurred on the map. Furthermore, the query utilizes a `CASE` statement to label sections of the map.
```postgresql
select a.interactionId,
       b.gameId         as gameId,
       b.gameTime       as gameTime,
       a.sourcePlayerId as sourcePlayerId,
       a.player1Id      as orginatingPlayer,
       a.player2Id      as playerBeingEngaged,
       b.playerId,
       b.leftCoordinate,
       b.topCoordinate,
       CASE
          WHEN b.leftCoordinate > 75 AND b.leftCoordinate < 450 AND b.topCoordinate > 375 AND b.topCoordinate < 450 THEN 'The Bridge'
          WHEN b.leftCoordinate > 400 AND b.leftCoordinate < 850 AND b.topCoordinate > 100 AND b.topCoordinate < 400 THEN 'Downtown'
          WHEN b.leftCoordinate > 425 AND b.leftCoordinate < 925 AND b.topCoordinate > 500 AND b.topCoordinate < 800 THEN 'Business District'
          WHEN b.leftCoordinate > 1000 AND b.leftCoordinate < 1200 AND b.topCoordinate > 200 AND b.topCoordinate < 850 THEN 'Amiko Greens'
          WHEN b.leftCoordinate > 1300 AND b.leftCoordinate < 1800 AND b.topCoordinate > 0 AND b.topCoordinate < 500 THEN 'Glen Falls Division'
          WHEN b.leftCoordinate > 1300 AND b.leftCoordinate < 1800 AND b.topCoordinate > 500 AND b.topCoordinate < 1100 THEN 'Kasama District'
          ELSE 'Other'
          END          AS Location
from interactions a
        INNER JOIN player_position b
                   on a.sourcePlayerId = b.playerId
where a.gameTime = b.gameTime
  and a.gameId = b.gameId
```
## Query 2 - Enriched Player Position
This sql creates reader-friendly labels for sections of coordinates. The stream provides where a coordinates and location of a player for a given point in time of the match (note: GameTime is number of milliseconds since the game simulation was initialized).
```postgresql
SELECT *,
       CASE
          WHEN leftCoordinate > 75 AND leftCoordinate < 450 AND topCoordinate > 375 AND topCoordinate < 450 THEN 'The Bridge'
          WHEN leftCoordinate > 400 AND leftCoordinate < 850 AND topCoordinate > 100 AND topCoordinate < 400 THEN 'Downtown'
          WHEN leftCoordinate > 425 AND leftCoordinate < 925 AND topCoordinate > 500 AND topCoordinate < 800 THEN 'Business District'
          WHEN leftCoordinate > 1000 AND leftCoordinate < 1200 AND topCoordinate > 200 AND topCoordinate < 850 THEN 'Amiko Greens'
          WHEN leftCoordinate > 1300 AND leftCoordinate < 1800 AND topCoordinate > 0 AND topCoordinate < 500 THEN 'Glen Falls Division'
          WHEN leftCoordinate > 1300 AND leftCoordinate < 1800 AND topCoordinate > 500 AND topCoordinate < 1100 THEN 'Kasama District'
          ELSE 'Other'
          END AS Location
FROM player_position
```
## Query 3 - Player Speed
The following calculates the player's speed. As you may remember, the way to do that is to divide the distance traveled by amount of time passed. The distance is calculated with the formula $\sqrt{(x<sub>1</sub>-x<sub>2</sub>)<sup>2</sup>+(y<sub>1</sub>-y<sub>2</sub>)<sup>2</sup>} and the coordinates from the current and previous player record. The delta of time is calculated from the current and previous record GameTime. Note: This is how we will be able to identify if there are any cheaters; if there is a player moving faster than others, we have good reason to suspect cheating.
```postgresql
SELECT a.recordId as recordId,
       a.gameId as gameId,
       a.playerId as playerId,
       a.gameTime as previousGametime,
       a.topCoordinate as previousTopCoordinate,
       a.leftCoordinate as previousLeftCoordinate,
       b.gameTime as currentGameTime,
       b.topCoordinate as currentTopCoordinate,
       b.leftCoordinate as currentLeftCoordinate,
       sqrt((b.leftCoordinate - a.leftCoordinate) * (b.leftCoordinate - a.leftCoordinate) + (b.topCoordinate - a.topCoordinate) * (b.topCoordinate - a.topCoordinate)) as distanceTraveled,
       abs(sqrt((b.leftCoordinate - a.leftCoordinate) * (b.leftCoordinate - a.leftCoordinate) + (b.topCoordinate - a.topCoordinate) * (b.topCoordinate - a.topCoordinate)) / (b.gameTime - a.gameTime) * 100) as speed
FROM player_position a
         RIGHT JOIN player_position b
                    on a.playerId = b.playerId
where a.recordId = b.recordId - 100
  and a.gameId = b.gameId
```

# Visualize with Streamlit

**Initial Spawn Visual.** This answers the question "Where are most players spawning at the beginning of the game? Do we need to consider a different distribution"
![Intial Spawn Visual](assets/initial-spawn.png)

**Average Speed Visual.** This helps identify if there are players moving faster than others (and indicator of cheating). As you can see in this visual and our dataset, Player 0 is moving 6x faster than other players.
![Average Speed Visual](assets/average-speed.png)

**Most Interactions.** This answers the question "Which players interact the most with other players?". This can help create player "style profiles" where in developers can understand players based on their style of play. It can also be a core component in matchmaking. The more interactions, the better the player. Players with interactions much higher than those in the same match problably need to be allocated to a batch of players that are on the same level.
![Most Interactions](assets/most-ineractions.png)

**Locations Visual.** This answers the question "Where are most player throughout the game?" For example, we can see that towards the end game of the match, most players were in the Business District and Other. Alternatively, at the beginning of the match, most players were at Amiko Greens.

![Location Visual](assets/player-time-by-location.png)
    
