CREATE TABLE IF NOT EXISTS Users(
  user_id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS Sessions(
  session_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES Users(user_id),
  client_address STRING NOT NULL,
  idle_since TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS RequestLog(
  request_id INTEGER PRIMARY KEY,
  session_id INTEGER REFERENCES Sessions(session_id),
  address STRING NOT NULL,
  direction BOOLEAN NOT NULL,
  time TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS Media(
  media_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES Users(user_id),
  type INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS Reports(
  report_id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES Users(user_id)
);
CREATE TABLE IF NOT EXISTS _ReportsMedia(
  report_id INTEGER NOT NULL REFERENCES Reports(report_id),
  media_id INTEGER NOT NULL REFERENCES Media(media_id),
  PRIMARY KEY(report_id, media_id)
);
CREATE TRIGGER IF NOT EXISTS check_report_media_user_insert
BEFORE INSERT ON _ReportsMedia
FOR EACH ROW BEGIN 
  SELECT RAISE(ABORT,'Report & media must belong to the same user.')
  WHERE(SELECT user_id FROM Reports WHERE report_id=NEW.report_id)!=
       (SELECT user_id FROM Media WHERE media_id=NEW.media_id);
END;
CREATE TRIGGER IF NOT EXISTS check_report_media_user_update
BEFORE UPDATE ON _ReportsMedia
FOR EACH ROW BEGIN
  SELECT RAISE(ABORT,'Report & media must belong to the same user.')
  WHERE(SELECT user_id FROM Reports WHERE report_id=NEW.reports_id)!=
       (SELECT user_id FROM Media WHERE media_id=NEW.media_id);
END;
