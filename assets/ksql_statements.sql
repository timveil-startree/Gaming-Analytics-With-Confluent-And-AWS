CREATE STREAM player_stream (
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
  sourcePlayerId INT,
  player1Id INT,
  player2Id INT

)
    WITH (
        KAFKA_TOPIC = 'interactions',
        VALUE_FORMAT = 'JSON'
    );


--Starting Positions
select  TOPCOORDINATE , LEFTCOORDINATE  from DATA_PLAYER where gameid = 3 and recordId between 0 and 39 EMIT CHANGES;



CREATE STREAM enriched_interactions_stream WITH (
        KAFKA_TOPIC = 'enriched_interactions_stream'
    ) AS 

    select 
    a.Interactionid,
    b.gameid as gameId,
    b.GAMETIME as GameTime,
    AS_VALUE(a.sourcePlayerId) as SourcePlayerId,
    a.player1Id as orginatingPlayer,
    a.player2Id as playerBeingEngaged,
    b.playerid,
    b.leftCoordinate,
    b. topCoordinate,
    CASE 
        WHEN b.LEFTCOORDINATE > 75 AND b.LEFTCOORDINATE < 450 AND b.TOPCOORDINATE > 375 AND b.TOPCOORDINATE < 450 THEN 'The Bridge'
        WHEN b.LEFTCOORDINATE > 400 AND b.LEFTCOORDINATE < 850 AND b.TOPCOORDINATE > 100 AND b.TOPCOORDINATE < 400 THEN 'Downtown'
        WHEN b.LEFTCOORDINATE > 425 AND b.LEFTCOORDINATE < 925 AND b.TOPCOORDINATE > 500 AND b.TOPCOORDINATE < 800 THEN 'Business District'
        WHEN b.LEFTCOORDINATE > 1000 AND b.LEFTCOORDINATE < 1200 AND b.TOPCOORDINATE > 200 AND b.TOPCOORDINATE < 850 THEN 'Amiko Greens'
        WHEN b.LEFTCOORDINATE > 1300 AND b.LEFTCOORDINATE < 1800 AND b.TOPCOORDINATE > 0 AND b.TOPCOORDINATE < 500 THEN 'Glen Falls Division'
        WHEN b.LEFTCOORDINATE > 1300 AND b.LEFTCOORDINATE < 1800 AND b.TOPCOORDINATE > 500 AND b.TOPCOORDINATE < 1100 THEN 'Kasama District'
        ELSE 'Other'

    END AS Location
    from INTERACTIONS_STREAM a
    INNER JOIN PLAYER_STREAM b
    WITHIN 1 HOURS on a.sourcePlayerId = b.playerid 
    where a.gametime = b.gametime
    and a.gameId = b.gameId
    EMIT CHANGES;



CREATE STREAM enriched_player_stream WITH (
        KAFKA_TOPIC = 'enriched_player_stream'
    )AS
   SELECT *, 
   CASE 
    WHEN LEFTCOORDINATE > 75 AND LEFTCOORDINATE < 450 AND TOPCOORDINATE > 375 AND TOPCOORDINATE < 450 THEN 'The Bridge'
    WHEN LEFTCOORDINATE > 400 AND LEFTCOORDINATE < 850 AND TOPCOORDINATE > 100 AND TOPCOORDINATE < 400 THEN 'Downtown'
    WHEN LEFTCOORDINATE > 425 AND LEFTCOORDINATE < 925 AND TOPCOORDINATE > 500 AND TOPCOORDINATE < 800 THEN 'Business District'
    WHEN LEFTCOORDINATE > 1000 AND LEFTCOORDINATE < 1200 AND TOPCOORDINATE > 200 AND TOPCOORDINATE < 850 THEN 'Amiko Greens'
    WHEN LEFTCOORDINATE > 1300 AND LEFTCOORDINATE < 1800 AND TOPCOORDINATE > 0 AND TOPCOORDINATE < 500 THEN 'Glen Falls Division'
    WHEN LEFTCOORDINATE > 1300 AND LEFTCOORDINATE < 1800 AND TOPCOORDINATE > 500 AND TOPCOORDINATE < 1100 THEN 'Kasama District'
    ELSE 'Other'

   END  AS Location
   FROM  player_stream 
   EMIT CHANGES;


CREATE STREAM PLAYER_STREAM_PREVIOUS_LOCATION WITH (
        KAFKA_TOPIC = 'player_stream_previous_location'
    )AS
   SELECT recordId - 100 as recordId,
   gameId,
  playerId,
  gameTime as previousGametime,
  topCoordinate as previousTopCoordinate,
  leftCoordinate as previousLeftCoordinate

   FROM  player_stream 
    EMIT CHANGES;


CREATE STREAM player_speed WITH (
        KAFKA_TOPIC = 'player_speed'
    )AS
    SELECT 
    a.recordId as recordId,
    a.gameId as gameId,
    AS_VALUE(b.playerId) as playerId,
    a.playerId,
    a.gameTime as currentGameTime,
    a.topCoordinate as currentTopCoordinate,
    a.leftCoordinate as currentLeftCoordinate,
   previousGametime, previousTopCoordinate, previousLeftCoordinate,
   sqrt((leftCoordinate-previousLeftCoordinate)*(leftCoordinate-previousLeftCoordinate)+(topCoordinate-previousTopCoordinate)*(topCoordinate-previousTopCoordinate)) as distanceTraveled,
   abs(sqrt((leftCoordinate-previousLeftCoordinate)*(leftCoordinate-previousLeftCoordinate)+(topCoordinate-previousTopCoordinate)*(topCoordinate-previousTopCoordinate))/(gameTime-previousGametime)*100) as speed
   FROM  player_stream a
    INNER JOIN player_stream_previous_location b
    WITHIN 1 HOURS on a.playerid = b.playerid
    where a.recordId = b.recordId
    and a.gameId = b.gameId
    
EMIT CHANGES;






drop stream player_speed;
drop stream PLAYER_STREAM_PREVIOUS_LOCATION;
drop stream enriched_player_stream;
drop stream enriched_interactions_stream;
drop stream player_stream;
drop stream interactions_stream;

 