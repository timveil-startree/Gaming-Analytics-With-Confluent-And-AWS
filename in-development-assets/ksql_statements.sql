CREATE STREAM player_data (
  recordId INT,
  gameId INT,
  playerId INT,
  gameTime INT,
  topCoordinate INT,
  leftCoordinate INT
)
    WITH (
        KAFKA_TOPIC = 'player-position',
        VALUE_FORMAT = 'JSON'
    );


CREATE STREAM interactions_stream (
  interactionId STRING,
  gameId INT,
  gameTime INT,
  playerId INT
)
    WITH (
        KAFKA_TOPIC = 'interactions',
        VALUE_FORMAT = 'JSON'
    );


--Starting Positions
select  TOPCOORDINATE , LEFTCOORDINATE  from DATA_PLAYER where gameid = 3 and recordId between 0 and 39 EMIT CHANGES;

--player encouunters
--Places mapped. load into Dynamodb and use arthematic and BETWEEN

--how to idenfitfy fast travelers to ban
select playerId, gameid,
STDDEV_SAMPLE(LEFTCOORDINATE),
STDDEV_SAMPLE( TOPCOORDINATE ) from DATA_PLAYER where gameid = 11
group by playerid, gameid EMIT CHANGES;





--consume 


