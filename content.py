"""Lecture-aligned practice; all figures are hypothetical value units."""
from math import log
from finance import Model

CASES={
 'one':dict(title='One period · price the right',m=Model(n=1,T=1),costs={1:100.},
  objective='Find the pricing weights and value a payoff that can be declined.',
  story='An asset is worth 100 today and will be worth 120 or 80 in one year. You can pay 100 at that date to acquire it. The effective annual risk-free rate is 5%.',
  source='Lecture sections 2–10',lesson='An option price is a value today, not an average payoff or the NPV after a license fee.',
  predict=('If the right costs 8 today, what should we compare with 8?', ['The current value of the right','The up-state payoff of 20','The underlying value of 100'],0,
   ['Yes. The right is worth 11.9048, so buying it for 8 creates net value 3.9048.','20 is one future payoff, not the value today.','100 is the whole operating asset, not the option to buy it.'])),
 'two':dict(title='Two periods · work backward',m=Model(),costs={2:100.},
  objective='Use future option values, rather than underlying values, in backward recursion.',
  story='The underlying starts at 100, rises by a factor of 1.2 or falls by 0.8 each year, and has no payouts. The right to pay 100 expires in two years. There is no intermediate investment gate. One dollar grows to 1.05 each year.',
  source='Lecture sections 11–13',lesson='At each earlier node, discount the weighted child option values. A zero immediate exercise payoff can coexist with a valuable future right.',
  predict=('At year 1, S = 120. Which two values belong in the option recursion?', ['The year-2 option payoffs, 44 and 0','The year-2 underlying values, 144 and 96','The year-1 immediate payoff, 20, in both states'],0,
   ['Correct: the claim being valued is the option.','Those values would price the underlying asset, before the final investment cost.','The European right is exercisable only in year 2; its remaining opportunity is what matters.'])),
 'gates-two':dict(title='Two periods · invest or stop',m=Model(),costs={0:5.,1:10.,2:100.},
  objective='Distinguish continuation value, the NPV of paying, and the option to stop.',
  story='Pay 5 today to start. In one year choose whether to pay 10 to retain access. In two years choose whether to pay 100 for the project. S starts at 100; u = 1.2, d = 0.8, and R = 1.05 each year. Stopping ends access permanently.',
  source='Lecture sections 17–22',lesson='Subtract a gate cost once, after valuing the remaining opportunity. A green zero means stop, not that paying has zero NPV.',
  predict=('What should be compared with the year-1 gate cost of 10?', ['The remaining launch option’s value','The underlying project value','The 5 already spent at date 0'],0,
   ['Correct. In the up state, paying 10 buys an option worth 26.1905.','You are buying continued access, not yet receiving the operating project.','The initial 5 is sunk at year 1; it does not determine the next decision.'])),
 'gates-three':dict(title='Three periods · follow the policy',m=Model(n=3,T=3),costs={0:5.,1:10.,2:10.,3:100.},
  objective='Explain a stop node and why a later profitable node may never be reached.',
  story='Use the lecture’s three-period extension: costs 5, 10, 10, and 100 at dates 0, 1, 2, and 3. S starts at 100; u = 1.2, d = 0.8, and R = 1.05 each year. Every payment is discretionary; there are no interim benefits or technical failures.',
  source='Lecture sections 23–24',lesson='Policies are conditional on reaching a node without a prior stop. Recombining underlying values do not restore an abandoned opportunity.',
  predict=('At year 2, S = 96 and continuation is about 9.05. The gate cost is 10. What does a green zero mean?', ['Stop; paying has a negative NPV','Pay; the investment breaks even','Wait one more year without paying the gate'],0,
   ['Correct: 9.0476 − 10 = −0.9524, while the option to stop is worth zero.','The NPV of paying is negative. The max operation clips the option value to zero.','There is no free waiting right here. Not paying ends access.'])),
 'four':dict(title='Four periods · separate steps from gates',m=Model(n=4,T=4),costs={0:3.,2:8.,4:100.},
  objective='Recognize that a time step is not necessarily an investment gate.',
  story='A new practice example: S = 100, u = 1.2, d = 0.8, R = 1.05 per year. Pay 3 today for access, optionally 8 at year 2, and optionally 100 at year 4. Years 1 and 3 are observation dates only: no payment or exercise is allowed there.',
  source='New four-period extension of the lecture',lesson='At observation-only dates, carry the discounted value. Apply the investment decision only at the specified gates.',
  predict=('What operation belongs at year 3?', ['Discount the two year-4 option values','Subtract another cost of 8','Exercise immediately for S − 100'],0,
   ['Correct. Year 3 is not a gate or an exercise date.','The 8 belongs only at year 2; do not charge it again.','Launch is available only at year 4 in this contract.'])),
}

RULES={
 'put_terminal':['F = max(0, K − S)','F = max(0, S − K)','F = K − S'],
 'european':['V = (p × Fu + (1 − p) × Fd) / R','V = max(S − K, 0)','V = p × Fu + (1 − p) × Fd'],
 'R':['R = exp(r × dt)','R = r × dt','R = 1 + r × dt'],
 'p':['p = (R − d) / (u − d)','p = the manager’s forecast','p = (u − R) / (u − d)'],
 'u':['u = exp(sigma × sqrt(dt))','u = exp(sigma × dt)','u = 1 + sigma'],
 'd':['d = 1 / u','d = 1 − u','d = exp(sigma × sqrt(dt))'],
 'dt':['dt = T / n','dt = T × n','dt = n / T'],
 'S':['S = parent × move','S = parent + move','S = parent / R'],
 'terminal':['F = max(0, S − K)','F = S − K','F = max(0, K − S)'],
 'C':['Cgo = (p × Fu + (1 − p) × Fd) / R','Cgo = (p × Su + (1 − p) × Sd) / R','Cgo = p × Fu + (1 − p) × Fd'],
 'net':['NPVpay = Cgo − K','NPVpay = max(0, Cgo − K)','NPVpay = Cgo − K − sunk'],
 'F':['F = max(0, Cgo − K)','F = Cgo − K','F = max(0, S − K)'],
}


def tasks(m,costs,terms,nodes):
    out=[]
    def add(id,kind,label,target,variables,expr,why,node=None,field=None):
        out.append(dict(id=id,kind=kind,label=label,target=target,vars=variables,expr=expr,why=why,node=node,field=field))
    add('R','R','Setup · growth factor R',terms['R'],dict(r=m.r,dt=terms['dt']),'exp(r*dt)','R is the future value of one dollar over one step. It is a growth factor, not a percentage.')
    add('p','p','Setup · pricing probability p',terms['p'],dict(R=terms['R'],u=terms['u'],d=terms['d']),'(R-d)/(u-d)','Pricing weights and risk-free discounting must be used together. The actual up probability is not needed.')
    # A missing underlying value tests construction before valuation.
    j=1 if m.n>1 else 0;i=m.n;parent=nodes[i-1,j if j<i else j-1]['S'];move=terms['u'] if j<i else terms['d']
    add('S','S',f'Underlying · step {i}, {j} down move(s)',nodes[i,j]['S'],dict(parent=parent,move=move),'parent*move','The same number of up and down moves produces the same underlying value, regardless of their order.',(i,j),'S')
    for i in range(m.n,-1,-1):
        for j in range(i+1):
            z=nodes[i,j];base=f'{i}-{j}';label=f'Step {i}, {j} down · '
            if i==m.n:
                if j==m.n:continue  # One known boundary anchors the incomplete tree.
                add(base+'-F','terminal',label+'final payoff F',z['F'],dict(S=z['S'],K=z['K']),'max(0,S-K)','At the final gate, exercise only if the operating asset is worth more than its cost.',(i,j),'F')
            else:
                a=nodes[i+1,j];b=nodes[i+1,j+1]
                add(base+'-C','C',label+'continuation Cgo',z['C'],dict(p=terms['p'],R=terms['R'],Fu=a['F'],Fd=b['F'],Su=a['S'],Sd=b['S']),'(p*Fu+(1-p)*Fd)/R','Discount the next-step option values. Their later investment costs have already been accounted for.',(i,j),'C')
                if i in costs:
                    add(base+'-net','net',label+'NPV of paying',z['net'],dict(Cgo=z['C'],K=z['K'],sunk=costs.get(0,0) if i else 0),'Cgo-K','This signed NPV can be negative. Do not clip it to zero until valuing the option to decline.',(i,j),'net')
                    add(base+'-F','F',label+'optimal net value F',z['F'],dict(Cgo=z['C'],K=z['K'],S=z['S']),'max(0,Cgo-K)','A negative NPV of paying leads to stopping and an option value of zero.',(i,j),'F')
    return out
