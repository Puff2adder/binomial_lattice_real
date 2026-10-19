"""Two-stage lecture problems: five input questions, then clickable values."""
import json,hashlib
from dataclasses import asdict
import streamlit as st
from builder import node_board
from finance import lattice,commitment
from builder_model import ready
from calculator import calculate
from content import CASES

def questions(m):
    return {
        'dt':('Δt · length of one period',['T / n','T × n','n / T'],'Divide total maturity by the number of periods.'),
        'u':('u · up-move factor',['1 + up_return','up_return','exp(up_return × dt)'],'A 20% increase multiplies the underlying by 1.20.'),
        'd':('d · down-move factor',['1 − down_loss','down_loss','1 / u'],'A 20% decrease multiplies the underlying by 0.80. These lecture moves are supplied returns, not reciprocal CRR moves.'),
        'R':('R · risk-free growth factor',['exp(r × dt)','r × dt','exp((r − q) × dt), for all q'],'r is the continuous annual risk-free rate. R is the future value of one dollar over one step.'),
        'p':('p · risk-neutral up probability',['(exp((r − q) × dt) − d) / (u − d)','(u − exp((r − q) × dt)) / (u − d)','The actual probability of an up move'],'Use pricing growth r − q and discount at r. q = 0 in these lecture examples; p is not a forecast.')}

def exercise_nodes(m,costs):
    terms,tree=lattice(m,costs);out={}
    for (i,j),z in tree.items():
        if i==m.n:
            variables=dict(S=z['S'],K=costs[i]);expr='max(0,S-K)'
            hint='At maturity the right is worth max(0,S-K). K is paid only if you exercise.'
        else:
            variables=dict(p=terms['p'],R=terms['R'],Vu=tree[i+1,j]['F'],Vd=tree[i+1,j+1]['F'])
            expr='(p*Vu+(1-p)*Vd)/R'
            hint='Value the remaining option by discounting its child values: (p*Vu+(1-p)*Vd)/R.'
            if i in costs:
                variables['G']=costs[i];expr=f'max(0,{expr}-G)'
                hint+=' Subtract this gate payment G, then take max with zero. Declining ends access.'
        out[i,j]=dict(**z,vars=variables,expr=expr,hint=hint)
    return terms,out

def fill_column(i,m,nodes,answers):
    """Only populate a column after the whole following column is available."""
    if not all(ready((i,j),answers,m.n) for j in range(i+1)):
        raise ValueError('Complete the next column first.')
    if not any(answers.get(f'{i},{j}',{}).get('status')=='correct' for j in range(i+1)):
        raise ValueError('First solve one value in this column yourself.')
    for j in range(i+1):
        answers.setdefault(f'{i},{j}',dict(value=nodes[i,j]['F'],status='column'))

def lesson(cid,config_for):
    case=CASES[cid];prefix=cid+'__compact_'
    st.title(case['title']);st.write(case['story'])
    st.caption('Learning objective: '+case['objective'])
    m,costs=config_for(cid,case)
    terms,nodes=exercise_nodes(m,costs)
    signature=json.dumps([asdict(m),costs],sort_keys=True)
    statekey=prefix+'state'
    if st.session_state.get(statekey,{}).get('signature')!=signature:
        for key in list(st.session_state):
            if key.startswith(prefix):del st.session_state[key]
        st.session_state[statekey]=dict(signature=signature,answers={},learned={},feedback=None,event=None,declined=[])
    state=st.session_state[statekey];answers=state['answers'];learned=state['learned']
    stage=st.radio('Workspace',['1 · Identify the five inputs','2 · Complete the lattice'],horizontal=True,key=prefix+'stage')
    st.caption(f'Raw data: S₀ = {m.S:g}; up return = {(m.u-1)*100:g}%; down loss = {(1-m.d)*100:g}%; T = {m.T:g} years; n = {m.n}; continuous r = {100*m.r:.6f}%; dividend/convenience yield q = 0%.')
    if stage.startswith('1'):
        st.caption('Choose the correct answer to reveal each numerical input. All five questions are multiple choice; no calculations need to be typed here.')
        for k,(label,options,why) in questions(m).items():
            offset=sum(map(ord,k))%3;choices=options[offset:]+options[:offset]
            left,right=st.columns([3,2]);choice=left.radio(label,choices,index=None,key=prefix+'quiz_'+k)
            if choice==options[0]:learned[k]=terms[k];right.success(f'{k} = {terms[k]:.6f}');right.caption(why)
            elif choice is not None:right.error('Try again. '+why)
            elif k in learned:right.success(f'{k} = {learned[k]:.6f} · previously identified')
        if len(learned)==5:st.success('All five inputs identified. Continue to the lattice.')
        def next_stage():st.session_state[prefix+'stage']='2 · Complete the lattice'
        st.button('Continue to the lattice',key=prefix+'next',on_click=next_stage)
        st.caption('You may explore the lattice or its worked view at any time.')
    else:
        st.markdown(' · '.join(f'**{k}:** {learned[k]:.6f}' if k in learned else f'**{k}:** ?' for k in questions(m)))
        st.caption('Click a value, enter an expression, and check it. Work from right to left. Supplied local inputs avoid repetitive arithmetic. Blue labels show payments; green/red node backgrounds mean proceed/stop.')
        full=st.checkbox('Show the full complete lattice values',key=prefix+'full')
        payload=[]
        for (i,j),z in nodes.items():
            nodeid=f'{i},{j}';done=full or nodeid in answers
            action={'Proceed':'Continue' if i<m.n else 'Exercise','Stop':'Abandon' if i<m.n else 'Expire','Carry value':'Hold','Indifferent':'Indifferent'}[z['action']]
            payload.append(dict(id=nodeid,i=i,j=j,S=z['S'],display=f'{z["F"]:.4f}' if done else '?',done=done,action=action if done else '',ready=ready((i,j),answers,m.n),vars=z['vars'] if full or ready((i,j),answers,m.n) else {},hint=z['hint'],solution=f'{z["expr"]} = {z["F"]:.6f}' if full else ''))
        offer=None
        feedback=state['feedback']
        if feedback and feedback['ok'] and m.n>=3 and not full:
            i=int(feedback['node'].split(',')[0])
            if i not in state['declined'] and any(f'{i},{j}' not in answers for j in range(i+1)) and all(ready((i,j),answers,m.n) for j in range(i+1)):
                offer=i
        event=node_board(nodes=payload,n=m.n,dt=terms['dt'],K=costs[m.n],costs={i:k for i,k in costs.items() if i<m.n},signature=cid+signature,reveal=full,feedback=feedback,offerColumn=offer,key=prefix+'board_'+hashlib.sha256(signature.encode()).hexdigest()[:12],default=None)
        if event and event.get('nonce')!=state['event']:
            state['event']=event['nonce']
            try:
                action=event.get('action','check')
                if action in ('fill_column','manual_column'):
                    i=int(event['column'])
                    if offer!=i:raise ValueError('Solve one value in this column first.')
                    if action=='fill_column':fill_column(i,m,nodes,answers)
                    state['declined'].append(i)
                    state['feedback']=dict(node=feedback['node'],ok=True,text='Remaining column values filled and marked as assisted.' if action=='fill_column' else 'Continue by clicking each cell in this column.')
                else:
                    nodeid=event['node'];pos=tuple(map(int,nodeid.split(',')));z=nodes[pos]
                    if not full and not ready(pos,answers,m.n):raise ValueError('Work from right to left: complete both child values first.')
                    value=calculate(event.get('expression',''),z['vars']);ok=abs(value-z['F'])<=.005
                    if ok:answers.setdefault(nodeid,dict(value=z['F'],status='revealed' if full else 'correct'))
                    message=f'Correct: {z["F"]:.6f}. '+z['action']+'.' if ok else 'Not quite. Check the payoff, discounting and any gate cost, then try again.'
                    if ok and pos[0] in costs and pos[0]<m.n:message+=f' Before the gate: {z["C"]:.6f}; signed NPV of paying: {z["net"]:.6f}. The option is max(0, NPV).'
                    state['feedback']=dict(node=nodeid,ok=ok,text=message)
            except (ValueError,KeyError) as e:state['feedback']=dict(node=event.get('node',''),ok=False,text=str(e))
            st.rerun()
        independent=sum(v['status']=='correct' for v in answers.values())
        st.caption(f'{independent} checked · {len(answers)-independent} assisted · {len(nodes)-len(answers)} remaining. Column completion is assisted practice.')
        if full or '0,0' in answers:
            root=nodes[0,0]
            if 0 in costs:
                a,b,c=st.columns(3);a.metric('Before initial payment',f'{root["C"]:.4f}');b.metric('Signed starting NPV',f'{root["net"]:.4f}');c.metric('Option to start',f'{root["F"]:.4f}')
            else:st.metric('Option value today',f'{root["F"]:.6f}')
        with st.expander('Worked solution and interpretation'):
            st.dataframe([{'Step':i,'Down moves':j,'Underlying':z['S'],'Inputs':', '.join(f'{k}={v:.6f}' for k,v in z['vars'].items()),'Expression':z['expr'],'Before payment':z['C'],'Payment':costs.get(i),'Signed NPV':z['net'] if i in costs else None,'Option value':z['F'],'Decision':z['action']} for (i,j),z in nodes.items()],hide_index=True)
            st.write(case['lesson'])
            st.caption(f'Fixed commitment NPV, assuming all payments are mandatory: {commitment(m,costs):.6f}. Stopping at a gate permanently ends access; later profitable nodes do not restore it.')
    st.session_state.progress[cid]=dict(signature=signature,formulas=dict(learned),answers=dict(answers))
