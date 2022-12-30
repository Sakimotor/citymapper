sql_schema = """create table nodes (
stop_i numeric ,
lat numeric,
lon numeric,
name text,
PRIMARY KEY (stop_i)
);
create table routes(
route_type NUMERIC,
route_name TEXT,
route_i NUMERIC, 
PRIMARY KEY (route_i)
);

create table walk (
from_stop_i numeric,
to_stop_i numeric,
duration_avg numeric,
route_i text,
PRIMARY KEY (from_stop_i, to_stop_i)
);
create table combined(
from_stop_i numeric,
to_stop_i numeric,
duration_avg numeric,
route_i numeric,
PRIMARY KEY (from_stop_i, to_stop_i, route_i),
FOREIGN KEY (route_i) references routes(route_i),
FOREIGN KEY (from_stop_i) references nodes(stop_i),
FOREIGN KEY (to_stop_i) references  nodes(stop_i)
);
create table temporal_day(
from_stop_i numeric,
to_stop_i numeric,
dep_time_ut numeric,
arr_time_ut numeric,
route_type numeric ,
seq numeric ,
route_i numeric,
PRIMARY KEY (from_stop_i, to_stop_i, dep_time_ut, arr_time_ut, route_i),
FOREIGN KEY (from_stop_i, to_stop_i, route_i) references combined(from_stop_i, to_stop_i, route_i)
);"""