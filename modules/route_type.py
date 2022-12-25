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


def str_route_num(route_nom):
    route_nom = str(route_nom).upper()
    if (route_nom == 'BUS') or (route_nom == 'FUNICULAR') or (route_nom == 'RAIL'):
        route = 3
    if route_nom == 'TRAM':
        route = 0
    if route_nom == 'METRO':
        route = 1
    return route
