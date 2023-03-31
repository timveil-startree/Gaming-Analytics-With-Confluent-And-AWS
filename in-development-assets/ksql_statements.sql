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

CREATE TABLE locations_tbl (
  locationId STRING PRIMARY KEY,
  locationName VARCHAR,
  leftMin INT,
  leftMax INT,
  topMin INT,
  topMAX INT
)
    WITH (
        KAFKA_TOPIC = 'Mongo.Game.Location',
        VALUE_FORMAT = 'JSON'
    );


select * from LOCATIONS_TBL EMIT CHANGES;
DROP TABLE LOCATIONS_TBL;



CREATE STREAM locations_enriched
    WITH (
        KAFKA_TOPIC = 'enriched_locations_stream'
    ) AS 

select 
a.Interactionid,
b.gameid,
b.GAMETIME,
b.playerid,
b.leftCoordinate,
b. topCoordinate
from INTERACTIONS_STREAM a
INNER JOIN DATA_PLAYER b
WITHIN 1 HOURS on a.playerid = b.playerid 
where a.gametime = b.gametime
and a.gameId = b.gameId
EMIT CHANGES;


CREATE STREAM locations_enriched
    WITH (
        KAFKA_TOPIC = 'enriched_locations_stream'
    ) AS 

select 
a.Interactionid,
b.gameid,
b.GAMETIME,
b.playerid,
b.leftCoordinate,
b. topCoordinate
from INTERACTIONS_STREAM a
INNER JOIN DATA_PLAYER b
WITHIN 1 HOURS on a.playerid = b.playerid 
INNER JOIN LOCATIONS_TBL c 
ON a
where a.gametime = b.gametime
and a.gameId = b.gameId
EMIT CHANGES;





