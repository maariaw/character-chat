CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE,
  password TEXT,
  role INTEGER,
  visible INTEGER
);

CREATE TABLE campaigns (
  id SERIAL PRIMARY KEY,
  title TEXT,
  creator_id INTEGER REFERENCES users,
  created_at TIMESTAMP,
  password TEXT,
  visible INTEGER
);

CREATE TABLE chats (
  id SERIAL PRIMARY KEY,
  title TEXT,
  campaign_id INTEGER REFERENCES campaigns,
  created_at TIMESTAMP,
  visible INTEGER
);

CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  message TEXT,
  user_id INTEGER REFERENCES users,
  chat_id INTEGER REFERENCES chats,
  sent_at TIMESTAMP,
  visible INTEGER
);

CREATE TABLE campaign_users (
  user_id INTEGER REFERENCES users,
  campaign_id INTEGER REFERENCES campaigns,
  visible INTEGER
);

CREATE TABLE "chat_users" (
  user_id INTEGER REFERENCES users,
  chat_id INTEGER REFERENCES chats,
  visible INTEGER
);
