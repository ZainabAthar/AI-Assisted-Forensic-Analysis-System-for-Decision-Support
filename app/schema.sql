CREATE TABLE Users(
  user_id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);
CREATE TABLE Media(
  media_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES Users(user_id),
  type INTEGER NOT NULL
);
CREATE TABLE Reports(
  report_id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES Users(user_id)
);
CREATE TABLE _ReportsMedia(
  report_id INTEGER NOT NULL REFERENCES Reports(report_id),
  media_id INTEGER NOT NULL REFERENCES Media(media_id),
  PRIMARY KEY(report_id, media_id)
);
CREATE TRIGGER check_report_media_user_insert
BEFORE INSERT ON _ReportsMedia
FOR EACH ROW BEGIN 
  SELECT RAISE(ABORT,'Report & media must belong to the same user.')
  WHERE(SELECT user_id FROM Reports WHERE report_id=NEW.report_id)!=
       (SELECT user_id FROM Media WHERE media_id=NEW.media_id);
END;
CREATE TRIGGER check_report_media_user_update
BEFORE UPDATE ON _ReportsMedia
FOR EACH ROW BEGIN
  SELECT RAISE(ABORT,'Report & media must belong to the same user.')
  WHERE(SELECT user_id FROM Reports WHERE report_id=NEW.reports_id)!=
       (SELECT user_id FROM Media WHERE media_id=NEW.media_id);
END;
CREATE TABLE Sessions(
  session_id INTEGER PRIMARY KEY,
  user_id INTEGER REFERENCES Users(user_id),
client_addr STRING NOT NULL,
idle_since TIMESTAMP
);
CREATE TRIGGER ssn_init_idle_since 
AFTER INSERT ON Sessions
BEGIN
  UPDATE Sessions
  SET idle_since = CURRENT_TIMESTAMP
  WHERE session_id = NEW.session_id;
END;
CREATE TABLE Requests(
  request_id INTEGER PRIMARY KEY,
  session_id INTEGER REFERENCES Sessions(session_id),
  method STRING NOT NULL,
  time TIMESTAMP
);
CREATE TRIGGER req_auto_timestamp
AFTER INSERT ON Requests
BEGIN 
  UPDATE Requests
  SET time = CURRENT_TIMESTAMP
  WHERE request_id = NEW.request_id;
END;
