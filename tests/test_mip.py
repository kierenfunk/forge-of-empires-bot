
import mip

def test_mip():

    # get population requirements

    m = mip.Model(sense=mip.MAXIMIZE)
    # name, ub, people, money per hour, size
    types = [
        ['Hut', float('inf'), 14, 6*12, 1],
        ['Long_house', 1, 70, 100, 2],
        ['Stilt_house', float('inf'), 22, 44, 1],
        ['Chalet', float('inf'), 32, 20, 1],
        ['Thatched', float('inf'), 27, 32, 1],
        ['Roof Tile', float('inf'), 44, 60, 1]
    ]

    x = [m.add_var(name=var[0], ub=var[1], var_type=mip.INTEGER) for var in types]
    m += mip.xsum(var*types[i][4] for i,var in enumerate(x)) <= 26 # number of buildings constraint
    m += mip.xsum(var*types[i][2] for i,var in enumerate(x)) >= 550 # people constraint
    m.objective = mip.xsum(var*types[i][3] for i,var in enumerate(x)) # (a*72)+(b*100)+(c*44)+(d*20)+(e*32)+(f*60)
    status = m.optimize()

    if status == mip.OptimizationStatus.OPTIMAL:
        print('optimal solution cost {} found'.format(m.objective_value))
    elif status == mip.OptimizationStatus.FEASIBLE:
        print('sol.cost {} found, best possible: {}'.format(m.objective_value, m.objective_bound))
    elif status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
        print('no feasible solution found, lower bound is: {}'.format(m.objective_bound))
    if status == mip.OptimizationStatus.OPTIMAL or status == mip.OptimizationStatus.FEASIBLE:
        print('solution:')
        total_pop = 0
        for i,v in enumerate(m.vars):
            if abs(v.x) > 1e-6: # only printing non-zeros
                total_pop += v.x*types[i][2]
                print('{} : {}'.format(v.name, v.x))
    print('current: ',(4*20)+(3*44)+100+(13*72))
    print(total_pop)