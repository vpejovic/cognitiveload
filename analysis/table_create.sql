CREATE TABLE user(        client_id       character varying(255)	PRIMARY KEY    NOT NULL,	age int,	sex_male boolean,	hand_right boolean,	education	ed_level,        n2_correct     int,        n2_incorrect   int,        n2_all_correct int,        n2_time_start      bigint,        n3_correct     int,        n3_incorrect   int,        n3_all_correct int,        n3_time_start      bigint,        sincerity	real,        fairness	real,        greed_avoidance	real,    	modesty	real,    	fearfulness real,    	anxiety    real,    	dependence    real,   	sentimentality    real,    	social_self_esteem    real,    	social_boldness    real,    	sociability    real,    	liveliness    real,    	forgiveness    real,    	gentleness    real,    	flexibility    real,    	patience    real,    	organization    real,    	diligence    real,    	perfectionism    real,    	prudence    real,    	aesthetic_appreciation    real,    	inquisitiveness    real,    	creativity    real,    	unconventionality    real,        honesty    real,        emotionality    real,        extraversion    real,        agreeableness    real,        conscientiousness    real,        openness    real );

CREATE TABLE primary_task(
	task_id	bigint	PRIMARY KEY	NOT NULL,
	client_id	character varying(255)    NOT NULL,
	type	tasktype	NOT NULL,
	label	difficulty,
	time_on_task	bigint,
	time_start	bigint,
	time_end	bigint,
	num_correct	int,
	num_incorrect	int,
	num_all_correct	int,
	task_load_index	int,
	finished	boolean
);

CREATE TABLE secondary_task(
	sec_task_id	bigint	PRIMARY KEY	NOT NULL,
	prim_task_id	bigint	REFERENCES primary_task(task_id),
	client_id	character varying(255)    NOT NULL,
	timestamp	bigint,
	opacity	double precision,
	finished	boolean
);

CREATE TYPE difficulty AS ENUM ('low', 'medium', 'high');

CREATE TYPE tasktype AS ENUM ('HP', 'FA', 'GC', 'NC', 'SX', 'PT', 'R');

CREATE TYPE ed_level AS ENUM ('I', 'II', 'III', 'IV', 'V', 'VI/1', 'VI/2', 'VII', 'VIII/1', 'VIII/2');
