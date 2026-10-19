"""Compact formula quiz and clickable node workbench."""
import json,hashlib
from pathlib import Path
from math import log,exp
from finance import black_scholes
import streamlit as st
import streamlit.components.v1 as components
from builder_model import build,ready
from calculator import calculate

node_board=components.declare_component('node_board',path=str(Path(__file__).parent/'lattice_component'))
FORMULAS={
 'dt':('Δt',['T / n','T × n','n / T'],'Divide the maturity into equal time steps.'),
 'u':('u',['exp(sigma × sqrt(dt))','exp(sigma × dt)','1 + sigma'],'CRR scales volatility by the square root of the time step.'),
 'd':('d',['1 / u','1 − u','exp(sigma × sqrt(dt))'],'CRR uses reciprocal up and down factors.'),
 'R':('R',['exp(r × dt)','exp((r − q) × dt)','r × dt'],'Discount at the risk-free rate r. R is the future value of one dollar.'),
 'p':('p',['(exp((r − q) × dt) − d) / (u − d)','(R − d) / (u − d), even when q ≠ 0','(u − exp((r − q) × dt)) / (u − d)'],'The underlying grows at r − q under pricing weights. p is not a forecast probability.')}

def setup():
    st.title('Build the lattice')
    st.caption('Identify the pricing inputs. Then click a node and value the option from right to left. Hypothetical values; at most four periods.')
    cols=st.columns(3)
    kind=cols[0].selectbox('Option',['Call','Put'],key='build_kind')
    style=cols[1].selectbox('Exercise',['European','American'],key='build_style')
    structure=cols[2].selectbox('Structure',['Simple','Compound (gates)'],key='build_structure')
    with st.expander('Problem data · change the example',expanded=False):
        a,b,c=st.columns(3)
        S=a.number_input('Underlying S₀',1.,1000.,100.,5.,key='build_S')
        K=b.number_input('Strike K',0.,1000.,100.,5.,key='build_K')
        n=c.selectbox('Periods n',[1,2,3,4],index=1,key='build_n')
        T=a.number_input('Maturity T (years)',.25,4.,1.,.25,key='build_T')
        r=b.number_input('Continuous r (%)',-5.,30.,100*log(1.05),.1,format='%.6f',key='build_r')/100
        sigma=c.number_input('Volatility sigma (%)',10.,80.,30.,1.,key='build_sigma')/100
        yield_q=a.number_input('Dividend / convenience yield q (%)',0.,30.,0.,.5,key='build_q')/100
        st.caption('q is a continuous proportional dividend or convenience yield, with zero storage cost in this example. R = exp(r × dt); the pricing growth factor is exp((r − q) × dt).')
        gates={}
        if structure!='Simple':
            dates=st.multiselect('Access-gate steps (before maturity)',list(range(n)),default=[n-1],key=f'build_dates_{n}')
            for i in dates:gates[i]=st.number_input(f'Gate payment G at step {i}',0.,500.,10.,1.,key=f'build_gate_{i}')
    st.write(f'S₀ = {S:g} · K = {K:g} · T = {T:g} years · n = {n} · r = {100*r:.4f}% · σ = {100*sigma:g}% · q = {100*yield_q:g}%')
    st.caption('q = continuous dividend or convenience yield. Pricing growth uses r − q; discounting uses r.')
    if structure!='Simple':
        st.caption('Gate G buys continued access; declining ends the opportunity. K is the exercise price and is paid only on exercise. '+('American exercise is available before each access payment: exercise now, or pay G to retain the option. Exercise ends future gates.' if style=='American' else 'Exercise occurs only at maturity; earlier gate payments buy access to that final right.'))
    try:terms,nodes=build(S,K,T,n,r,sigma,yield_q,kind,style,gates)
    except ValueError:
        st.error('These inputs do not form an arbitrage-free tree. Require d < exp((r − q) × dt) < u. Increase the number of periods or adjust the data.');return
    sig=json.dumps([S,K,T,n,r,sigma,yield_q,kind,style,gates],sort_keys=True)
    if st.session_state.get('build_signature')!=sig:
        for key in list(st.session_state):
            if key.startswith('build_quiz_'):del st.session_state[key]
        st.session_state.update(build_signature=sig,build_answers={},build_formulas={},build_feedback=None,build_event=None,build_reveal=False)
    def restart():
        st.session_state.pop('build_signature',None)
    top=st.columns([4,1]);stage=top[0].radio('Workspace',['1 · Translate the data','2 · Complete the lattice'],index=1,horizontal=True,key='build_stage')
    top[1].button('Restart practice',on_click=restart)
    learned=st.session_state.build_formulas;answers=st.session_state.build_answers
    if stage.startswith('1'):
        st.caption('Choose each formula. A correct choice reveals its numerical value; a wrong choice lets you try again.')
        for index,(name,(label,options,why)) in enumerate(FORMULAS.items()):
            left,right=st.columns([3,2]);offset=(index+1)%3;choices=options[offset:]+options[:offset]
            choice=left.radio(label,choices,index=None,key='build_quiz_'+name)
            if choice==options[0]:
                learned[name]=terms[name];right.success(f'{label} = {terms[name]:.6f}');right.caption(why)
            elif choice is not None:right.error('Try again. '+why)
            elif name in learned:right.success(f'{label} = {learned[name]:.6f} · previously identified')
        st.info('When ready, select “2 · Complete the lattice” above. You may also explore it before completing every formula.')
    else:
        st.markdown(' · '.join(f'**{k}:** {learned[k]:.6f}' if k in learned else f'**{k}:** ?' for k in FORMULAS))
        if len(learned)<5:st.caption('Unrevealed factors can be identified in “Translate the data”. Correct local inputs are supplied when you select a node.')
        st.caption('Black: underlying. Red: option value. At a gate, the value includes the choice to abandon. Complete the two connected child values before an earlier node.')
        reveal=st.checkbox('Show worked lattice',key='build_reveal')
        payload=[]
        for (i,j),z in nodes.items():
            nodeid=f'{i},{j}';done=nodeid in answers or reveal
            hint=('Use max(0, S − K) for a call or max(0, K − S) for a put.' if i==n else 'Discount the child option values: (p*Vu + (1-p)*Vd)/R. '+('At this gate, subtract G and take max with zero. ' if i in gates else '')+('For American exercise, also compare with the immediate exercise payoff.' if style=='American' else 'Do not exercise early.'))
            payload.append(dict(id=nodeid,i=i,j=j,S=z['S'],display=f'{z["value"]:.4f}' if done else '?',done=done,action=z['action'] if done else '',ready=ready((i,j),answers,n),vars=z['vars'] if ready((i,j),answers,n) or reveal else {},hint=hint,solution=f'{z["expr"]} = {z["value"]:.6f}' if reveal else ''))
        event=node_board(nodes=payload,n=n,dt=terms['dt'],K=K,costs=gates,signature=sig,reveal=reveal,feedback=st.session_state.build_feedback,key='build_board_'+hashlib.sha256(sig.encode()).hexdigest()[:12],default=None)
        if event and event.get('nonce')!=st.session_state.build_event:
            st.session_state.build_event=event['nonce'];nodeid=event.get('node','')
            try:
                pos=tuple(map(int,nodeid.split(',')));z=nodes[pos]
                if not ready(pos,answers,n) and not reveal:raise ValueError('Work from right to left: complete both child nodes first.')
                value=calculate(event.get('expression',''),z['vars'])
                ok=abs(value-z['value'])<=.005
                if ok:answers[nodeid]=dict(value=z['value'],status='revealed' if reveal else 'correct')
                message=f'Correct: {z["value"]:.6f}. {z["action"]}. Choose another node.' if ok else 'Not quite. Check the payoff, discounting, and any exercise or gate decision; then try again.'
                if ok and pos[0] in gates:message+=f' NPV of paying G = {z["net"]:.6f}; the option value includes the right to decline.'
                st.session_state.build_feedback=dict(node=nodeid,ok=ok,text=message)
            except (ValueError,KeyError):st.session_state.build_feedback=dict(node=nodeid,ok=False,text='Check your expression and use only the displayed inputs. Work from right to left.')
            st.rerun()
        st.caption(f'{len(answers)} of {len(nodes)} node values completed. Showing worked values is assisted practice.')
        if '0,0' in answers or reveal:st.metric(f'{style} {kind.lower()} · value today',f'{nodes[0,0]["value"]:.6f}')
        if reveal:
            with st.expander('Worked calculations and gate NPVs'):
                st.dataframe([{'Step':i,'Down':j,'S':z['S'],'Expression':z['expr'],'Value':z['value'],'NPV of gate payment':z['net'] if i in gates else None,'Action':z['action']} for (i,j),z in nodes.items()],hide_index=True)
        if structure=='Simple':
            with st.expander('Optional · compare one to four periods and Black–Scholes'):
                rows=[]
                for nn in range(1,5):
                    try:
                        _,z=build(S,K,T,nn,r,sigma,yield_q,kind,style)
                        rows.append({'Periods':nn,'Option value':z[0,0]['value']})
                    except ValueError:pass
                st.dataframe(rows,hide_index=True)
                bs=black_scholes(S*exp(-yield_q*T),K,T,r,sigma)
                if kind=='Put':bs-=S*exp(-yield_q*T)-K*exp(-r*T)
                st.write(f'European Black–Scholes {kind.lower()} with these inputs: {bs:.6f}.')
                st.caption('One to four steps are coarse and may oscillate. Black–Scholes is a European benchmark; American exercise can add value.')
    st.session_state.progress['setup']=dict(signature=sig,formulas=dict(learned),answers=dict(answers))
