def str_route_type(route_type):
    route_type = int(route_type)
    if route_type == 0:
        route = 'TRAM'
    elif route_type == 1:
        route = 'METRO'
    elif route_type == 2:
        route = 'RER'
    elif route_type == 3:
        route = 'BUS'
    else:
        route = 'ERROR'
    return route
