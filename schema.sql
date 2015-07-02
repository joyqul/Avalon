drop table if exists users;
create table users(
    id integer primary key autoincrement,
    username text not null,
    password text not null,
    win integer,
    lose integer
);

drop table if exists games;
create table games(
    id integer primary key autoincrement,
    result text not null,
    player0 integer not null,
    player1 integer not null,
    player2 integer not null,
    player3 integer not null,
    player4 integer not null,
    player5 integer,
    player6 integer,
    player7 integer,
    player8 integer,
    player9 integer,
    playerCount integer not null,
    findMerlin boolean not null,
    foreign key(player0) references players(id),
    foreign key(player1) references players(id),
    foreign key(player2) references players(id),
    foreign key(player3) references players(id),
    foreign key(player4) references players(id),
    foreign key(player5) references players(id),
    foreign key(player6) references players(id),
    foreign key(player7) references players(id),
    foreign key(player8) references players(id),
    foreign key(player9) references players(id)
);

drop table if exists players;
create table players(
    id integer primary key autoincrement,
    role text not null,
    userId integer not null,
    voteId integer not null,
    questId integer not null,
    assignId integer not null,
    ordering integer not null,
    foreign key(userId) references users(id),
    foreign key(voteId) references votes(id),
    foreign key(questId) references quests(id),
    foreign key(assignId) references assign(id)
);
    
drop table if exists votes;
create table votes(
    id integer primary key autoincrement,
    vote00 integer,
    vote01 integer,
    vote02 integer,
    vote03 integer,
    vote04 integer,
    vote05 integer,
    vote06 integer,
    vote07 integer,
    vote08 integer,
    vote09 integer,
    vote10 integer,
    vote11 integer,
    vote12 integer,
    vote13 integer,
    vote14 integer,
    vote15 integer,
    vote16 integer,
    vote17 integer,
    vote18 integer,
    vote19 integer,
    vote20 integer,
    vote21 integer,
    vote22 integer,
    vote23 integer,
    vote24 integer
);

drop table if exists assign;
create table assign(
    id integer primary key autoincrement,
    assign00 text,
    assign01 text,
    assign02 text,
    assign03 text,
    assign04 text,
    assign05 text,
    assign06 text,
    assign07 text,
    assign08 text,
    assign09 text,
    assign10 text,
    assign11 text,
    assign12 text,
    assign13 text,
    assign14 text,
    assign15 text,
    assign16 text,
    assign17 text,
    assign18 text,
    assign19 text,
    assign20 text,
    assign21 text,
    assign22 text,
    assign23 text,
    assign24 text
);

drop table if exists quests;
create table quests(
    id integer primary key autoincrement,
    quest0 boolean,
    quest1 boolean,
    quest2 boolean,
    quest3 boolean,
    quest4 boolean
);
