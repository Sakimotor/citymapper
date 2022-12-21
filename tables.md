So far I would say:

- **nodes**: stop_i
- **routes**: route_i
- **route_rps** : route_i -> routes where route_i = min(route_i) : foreign keys, relation 0..1 between route_rps and route_i
- **walk** : (from_stop_i, to_stop_i) -> foreign keys from **nodes** ? also route_i serves no purpose since walking routes have no actual id
- **short_walk** : (from_stop_i, to_stop_i) -> walk where d < 300 -> foreign keys
- **combined** : (from_stop_i, to_stop_i, route_i) -> we can go from one stop to another with multiple routes, foreign keys from nodes and routes
-- **stopxroute** : (stop_i, route_i) -> associates a stop with all its routes, foreign keys from combined (stop_i = from_stop_i UNION to_stop_i)
- **stoproutename** : stop_i -> takes stops from combined and names from (stopxroute inner join nodes inner join routes), all keys are foreign
-- **combxwalk** : (from_stop_i, to_stop_i, route_i) -> concatenation of walk x combined, all keys are foreign 
- **temporal_day**: (from_stop_i, to_stop_i, dep_time_ut, arr_type_ut) -> same
- **super_route_comb** : (from_stop_i, to_stop_i) , the keys from this table are all foreign keys from routexsuper and combined
- **routexsuper** :


