CREATE DATABASE 460_project;
USE 460_project;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;
DROP TABLE Albums CASCADE;
DROP TABLE Comments CASCADE;
DROP TABLE Friends CASCADE;
DROP TABLE Likes CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT,
    email varchar(255) UNIQUE,
    password varchar(255),
    first_name varchar(255),
    last_name varchar(255),
    gender CHAR(1),
    dob DATE,
    hometown varchar(255),
    p_count int4 DEFAULT 0,
    c_count int4 DEFAULT 0,,
    likes int4 DEFAULT 0,
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  a_id int11,
  tag1 VARCHAR(255),
  tag2 VARCHAR(255),
  tag3 VARCHAR(255),
  tag4 VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  FOREIGN KEY user_id REFERENCES Users(user_id),
  FOREIGN KEY a_id REFERENCES Albums(a_id),
  ON DELETE CASCADE
);

CREATE TABLE Albums (
    a_id int11  AUTO_INCREMENT NOT NULL UNIQUE,
    a_name varchar(255),
    doc DATE,
    user_id int11,
  FOREIGN KEY user_id REFERENCES Users(user_id),
  ON DELETE CASCADE
);

CREATE TABLE Comments (
    c_id int11 AUTO_INCREMENT NOT NULL UNIQUE,
    c_text TEXT,
    c_date DATE,
    user_id int11,
  FOREIGN KEY user_id REFERENCES Users(user_id)
);

CREATE TABLE Friends (
    user_id int11,
    f_email varchar(255),
  FOREIGN KEY user_id REFERENCES Users(user_id),
  FOREIGN KEY f_email REFERENCES Users(email),
);

CREATE TABLE Likes (
    user_id int11,
    picture_id int11,
    locked Char(1) DEFAULT 'N',
    FOREIGN KEY user_id REFERENCES Users(user_id),
    FOREIGN KEY picture_id REFERENCES Pictures(picture_id)
);
