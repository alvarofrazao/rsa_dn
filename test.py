import math

core_positions = (40.83548605,-7.99394846)

def generate_cells(start_lat, start_long, distance, n):

    planetary_radius = 6371.0  # in kilometers

    increment = distance/n

    directions = [(1,1),(1,-1),(-1,-1),(-1,1)] # NE,NW,SW,SE
    grid_quarters = []

    # Compute latitude variation
    delta_latitude = math.degrees(increment / planetary_radius)

    # Compute longitude variation
    delta_longitude = math.degrees(math.asin(
        math.sin(math.radians(delta_latitude)) / math.cos(math.radians(start_lat))))

    for dir in directions:
        grid = [[(0.0, 0.0) for _ in range(n)] for _ in range(n)]
        for lat_idx in range(0, n): # row iteration (latitude variation)
            for long_idx in range(0,n): #column iteration (longitude variation)
                grid[lat_idx][long_idx] = (start_lat+(dir[0]*(delta_latitude*lat_idx)),start_long+(dir[1]*(delta_longitude*long_idx)))
        grid_quarters.append(grid)
    return grid_quarters

def gen_centers(cell_grid, n):
    
    centers = []
    for a in range(0,n-2):
        for b in range(0,n-2):
            latitudes = [math.radians(lat) for lat,_ in [cell_grid[a][b],cell_grid[a+1][b],cell_grid[a][b+1],cell_grid[a+1][b+1]]]
            longitudes = [math.radians(long) for _,long in [cell_grid[a][b],cell_grid[a+1][b],cell_grid[a][b+1],cell_grid[a+1][b+1]]]

            avg_lat = math.degrees(sum(latitudes)/4)
            avg_long = math.degrees(sum(longitudes)/4)

            centers.append((avg_lat,avg_long))

    return centers

grid = generate_cells(core_positions[0],core_positions[1],3,5)
print(grid)

centers = gen_centers(grid[0],5)
print(centers)