DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS income;
DROP TABLE IF EXISTS expense;
DROP TABLE IF EXISTS balance;
DROP TABLE IF EXISTS budget;
DROP TABLE IF EXISTS saving_plan;
DROP TABLE IF EXISTS saving_account;
DROP TABLE IF EXISTS investment;
DROP TABLE IF EXISTS investment_track;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    registered TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    start_date DATE,
    end_date DATE,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'RMB',
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE expense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    start_date DATE,
    end_date DATE,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'RMB',
    details TEXT,
    source TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE balance (
    user_id INTEGER NOT NULL,
    updated_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'RMB',
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE budget (
    user_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (project_id) REFERENCES project (id)
);

CREATE TABLE saving_plan (
    user_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'RMB',
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id)
);


CREATE TABLE saving_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL DEFAULT 'RMB',
    details TEXT,
    project_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE investment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT,
    details TEXT,
    invest_date DATE NOT NULL,
    amount REAL,
    unit TEXT DEFAULT 'RMB',
    status TEXT CHECK(status='closed' or status='ongoing'),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE investment_track (
    investment_id INTEGER NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount REAL,
    unit TEXT DEFAULT 'RMB',
    FOREIGN KEY (investment_id) REFERENCES investment (id)
);


