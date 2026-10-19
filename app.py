"""Ungraded, lecture-aligned binomial and compound-option learning studio."""
from dataclasses import replace,asdict
from math import log,exp
from html import escape
import json,hashlib,io,csv,base64
import streamlit as st
from finance import Model,lattice,black_scholes,commitment,european_lattice
from calculator import calculate
from content import CASES,RULES,tasks
from questions import QUESTIONS

st.set_page_config(page_title='Binomial Decisions Studio',page_icon='🌳',layout='wide')
st.markdown('''<style>
.stApp{background:#fff;color:#142B49;color-scheme:light}
[data-testid="stSidebar"]{background:#EAF4FF}
h1,h2,h3{color:#0756A3!important}
[data-testid="stMarkdownContainer"],[data-testid="stCaptionContainer"],[data-testid="stWidgetLabel"]{color:#142B49!important;opacity:1!important}
input,textarea,[data-baseweb="select"]>div{background:white!important;color:#142B49!important}
:focus-visible{outline:3px solid #007F86!important;outline-offset:3px}
.block-container{padding-top:1.8rem;max-width:1500px}
[data-testid="stMetric"]{background:#EAF4FF;border-radius:8px;padding:12px}
[data-testid="stMetricValue"]{font-size:1.5rem}
button{min-height:40px}
[data-testid="stAppDeployButton"]{display:none}
</style>''',unsafe_allow_html=True)
ROUTES={'home':'Start here','setup':'Build the lattice'}|{k:v['title'] for k,v in CASES.items()}|{'applications':'Small experiments','practice':'Interpretation practice'}
if 'route' not in st.session_state:
    st.session_state.route=st.query_params.get('page','home') if st.query_params.get('page','home') in ROUTES else 'home'
st.session_state.setdefault('progress',{})
st.session_state.setdefault('configs',{})
with st.sidebar:
    st.title('Binomial decisions')
    st.caption('Peter Ritchken · Executive MBA')
    route=st.radio('Learning route',list(ROUTES),format_func=ROUTES.get,key='route')
    st.divider()
    st.markdown('**Think → calculate → interpret**\n\nAll problems have one to four periods. You can navigate freely or request a worked solution.')
    st.caption('Ungraded practice. No identity collection or grade transmission. Progress lasts only in this browser session; download it before leaving if needed.')
    st.download_button('Download my practice record',json.dumps(st.session_state.progress,indent=2),file_name='binomial_practice.json',mime='application/json')
st.query_params['page']=route


def reset(prefix):
    for k in list(st.session_state):
        if k.startswith(prefix+'__'):del st.session_state[k]
    st.session_state.progress.pop(prefix,None)
    st.session_state.configs.pop(prefix,None)


def register(prefix,signature):
    old=st.session_state.progress.get(prefix)
    if not old or old.get('signature')!=signature:
        for k in list(st.session_state):
            if k.startswith(prefix+'__work_') or k.startswith(prefix+'__prediction') or k.startswith(prefix+'__solution'):
                del st.session_state[k]
        st.session_state.progress[prefix]=dict(signature=signature,answers={},attempts=0)
    return st.session_state.progress[prefix]


def expression_task(task,prefix,record):
    """Formula selection plus symbolic entry; target symbol is never supplied."""
    key=prefix+'__work_'+task['id'];saved=record['answers'].get(task['id'],{})
    st.subheader(task['label'])
    if saved:
        st.caption('Value checked and placed.' if saved['status']=='correct' else 'Worked answer requested; recorded as assisted.')
    opts=RULES[task['kind']]
    # Rotate by stable task id, so the first option is not always correct.
    offset=sum(ord(c) for c in task['id'])%len(opts);ordered=opts[offset:]+opts[:offset]
    rule=st.selectbox('1 · Choose the economic rule',ordered,index=None,placeholder='Choose a rule',key=key+'_rule')
    st.caption('2 · Enter a number or an expression. Decimal p: 0.625, not 62.5. Use exp, log, sqrt, max, min, +, −, *, /, and ^.')
    expression=st.text_input('My value or expression',key=key+'_expression',placeholder='For example: (p*Fu+(1-p)*Fd)/R')
    c1,c2,c3=st.columns(3)
    if c1.button('Evaluate arithmetic',key=key+'_evaluate'):
        try:st.session_state[key+'_message']=('info',f"Arithmetic result: {calculate(expression,task['vars']):.8f}. This evaluates your expression; it does not yet check your reasoning.")
        except ValueError as e:st.session_state[key+'_message']=('error',str(e))
    if c2.button('Check and place',key=key+'_check',type='primary'):
        record['attempts']+=1
        try:
            value=calculate(expression,task['vars'])
            tolerance=.0006 if task['kind'] in ('R','p','u','d','dt') else .02
            if rule!=opts[0]:
                st.session_state[key+'_message']=('error','Reconsider the rule before placing the number. '+task['why'])
            elif abs(value-task['target'])>tolerance:
                diagnostic=''
                if task['kind']=='C' and abs(value-task['target']*task['vars']['R'])<.02:diagnostic='You have the weighted future value; divide by R to bring it back one step. '
                if task['kind']=='F' and value<0:diagnostic='The NPV of paying can be negative, but the option to stop is worth zero. '
                if task['kind']=='p' and value>1:diagnostic='Use a decimal probability between 0 and 1. '
                st.session_state[key+'_message']=('error',diagnostic+'The value does not match yet. Check the symbols and use the hint or arithmetic helper.')
            else:
                assisted=saved.get('status')=='revealed'
                record['answers'][task['id']]=dict(status='revealed' if assisted else 'correct',value=task['target'])
                st.session_state[key+'_message']=('success','Placed in the lattice. '+task['why'])
                st.rerun()
        except ValueError as e:st.session_state[key+'_message']=('error',str(e))
    if c3.button('Show this answer',key=key+'_reveal'):
        record['answers'][task['id']]=dict(status='revealed',value=task['target'])
        st.session_state[key+'_message']=('info',f"{task['expr']} = {task['target']:.8f}. "+task['why'])
        st.rerun()
    if key+'_message' in st.session_state:
        level,msg=st.session_state[key+'_message'];getattr(st,level)(msg)
    with st.expander('Calculation inputs · official values for this local step',expanded=True):
        st.code('   '.join(f'{k} = {v:.8g}' for k,v in task['vars'].items()),language=None)
        st.caption('These supplied local inputs remove repetitive arithmetic. They do not mark other lattice cells complete. The target value itself is not supplied.')
    with st.expander('Hint · what are we valuing?'):
        st.write(task['why'])
    with st.expander('Worked calculation · available on request'):
        st.code(task['expr'],language=None)
        st.write(f"Result: **{task['target']:.8f}**. "+task['why'])


def tree_svg(m,costs,q,nodes,tasklist,answers,selected=None,reveal=False,option_kind=None):
    masks={(t['node'],t['field']):t['id'] for t in tasklist if t['node'] is not None}
    def known(node,field):
        if not reveal and field=='C' and node[0]==m.n and not known(node,'S'):return False
        return reveal or (node,field) not in masks or masks[node,field] in answers
    def val(node,field):return f"{nodes[node][field]:.2f}" if known(node,field) else '?'
    def hasF(i,j):return known((i,j),'F') if i in costs else known((i,j),'C')
    W=210*m.n+190;H=100+96*m.n+95
    xy=lambda i,j:(90+210*i,75+48*(m.n-i+2*j))
    out=[f'<div style="overflow-x:auto;padding:6px 0" aria-label="Scrollable lattice"><svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {W} {H}" style="font-family:Arial,sans-serif;min-width:{W}px;max-height:{H}px" role="img" aria-label="Incomplete lattice. Question marks indicate missing values. Use the task selector below to fill a cell."><title>Incomplete binomial lattice</title>']
    for i in range(m.n):
        for j in range(i+1):
            x,y=xy(i,j)
            for k in (j,j+1):
                xx,yy=xy(i+1,k);out.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="#8DA7BA"/>')
    for i in range(m.n+1):
        out.append(f'<text x="{xy(i,0)[0]}" y="22" text-anchor="middle" fill="#142B49" font-size="14">Date {i*q["dt"]:g} · step {i}</text>')
        for j in range(i+1):
            key=(i,j);z=nodes[key];x,y=xy(i,j);gate=i in costs;done=hasF(i,j)
            bg=('#E4F3EC' if z['action']=='Proceed' else '#FBEAEC' if z['action']=='Stop' else '#FFF4D9') if gate and done else '#FFFFFF'
            stroke='#007F86' if selected==key else '#9BAFBD';width=3 if selected==key else 1
            out.append(f'<rect x="{x-77}" y="{y-41}" width="154" height="82" rx="8" fill="{bg}" stroke="{stroke}" stroke-width="{width}"/>')
            rows=[(f'S = {val(key,"S")}','#142B49')]
            if option_kind:
                field='F' if i==m.n else 'C'
                rows += [(f'{"Payoff" if i==m.n else option_kind.title()} = {val(key,field)}','#AA2435'),('Exercise at maturity' if i==m.n else 'No early exercise','#142B49'),(f'Node ({i},{j})','#142B49')]
            elif gate:
                rows += [(f'{"Receive" if i==m.n else "Cgo"} = {val(key,"C")}','#AA2435'),(f'F = {val(key,"F")}','#006A49'),(z['action'] if done else 'Decision ?', '#142B49')]
            else:
                field='F' if i==m.n else 'C';rows += [(f'Value = {val(key,field)}','#AA2435'),('No payment gate','#142B49'),(f'Node ({i},{j})','#142B49')]
            for k,(txt,color) in enumerate(rows):out.append(f'<text x="{x}" y="{y-23+k*18}" text-anchor="middle" fill="{color}" font-family="Arial,sans-serif" font-size="13">{escape(txt)}</text>')
        K=costs.get(i);out.append(f'<text x="{xy(i,0)[0]}" y="{H-20}" text-anchor="middle" fill="#0756A3" font-size="14">{("K = "+format(K,"g")) if K is not None else "No gate"}</text>')
    out.append('</svg></div>')
    markup=''.join(out)
    svg=markup[markup.index('<svg'):markup.index('</svg>')+6]
    data=base64.b64encode(svg.encode()).decode()
    # Streamlit sanitizes raw SVG in st.html. Embed a self-contained SVG image.
    return f'<div style="overflow-x:auto;padding:6px 0"><img src="data:image/svg+xml;base64,{data}" alt="Incomplete lattice. Question marks indicate missing values. Use the task selector to fill a cell." style="width:100%;min-width:{W}px;max-height:{H}px" /></div>'


def prediction(c,prefix):
    prompt,options,correct,feedback=c['predict']
    with st.expander('First, make the economic distinction',expanded=True):
        answer=st.radio(prompt,options,index=None,key=prefix+'__prediction_choice')
        if st.button('Check interpretation',key=prefix+'__prediction_check'):
            if answer is None:st.info('Choose an answer first.')
            else:
                idx=options.index(answer);(st.success if idx==correct else st.error)(feedback[idx])


def config_for(cid,c):
    m=c['m'];costs=c['costs'].copy();saved=st.session_state.configs.get(cid)
    if saved:m=Model(**saved['model']);costs={int(k):v for k,v in saved['costs'].items()}
    st.button('Reset to lecture example' if cid!='four' else 'Reset to four-period example',key=cid+'__reset',on_click=reset,args=(cid,))
    with st.expander('Change a cost or value · answers reset when applied'):
        with st.form(cid+'__input_form'):
            S=st.number_input('Underlying value today',min_value=1.,max_value=1000.,value=m.S,step=5.,key=cid+'__input_S')
            columns=st.columns(len(costs));newcosts={}
            for col,(i,K) in zip(columns,sorted(costs.items())):
                newcosts[i]=col.number_input(f'Cost at step {i}',min_value=0.,max_value=1000.,value=float(K),step=1.,key=cid+f'__input_K{i}')
            if st.form_submit_button('Apply inputs and clear answers'):
                st.session_state.configs[cid]={'model':asdict(replace(m,S=S)),'costs':newcosts};st.rerun()
    return m,costs


def lesson(cid):
    from guided import lesson as guided_lesson
    guided_lesson(cid,config_for)


from builder import setup


def applications():
    st.title('Small experiments')
    presets={
        'A more expensive development gate':('gates-two',{0:5.,1:20.,2:100.},'Can a later continuation be worthwhile while starting today is unattractive?'),
        'An expensive initial license':('one',{0:13.,1:100.},'Does a positive option value necessarily justify its price?'),
        'Free access between gates':('four',{0:3.,2:8.,4:100.},'Which dates require a decision, and which only require discounting?'),
    }
    name=st.selectbox('Choose the decision',list(presets),key='experiment')
    cid,costs,prompt=presets[name];m=CASES[cid]['m'];q,z=lattice(m,costs)
    st.write(prompt);st.write(f'Inputs: S₀ = {m.S:g}; u = {m.u:g}; d = {m.d:g}; R = {q["R"]:.2f}; {m.n} one-year periods. Gate costs: '+', '.join(f'date {i}: {v:g}' for i,v in costs.items()))
    choice=st.radio('Your initial recommendation',['Begin / buy access','Decline / do not start'],index=None,key='application_prediction_'+name)
    if st.button('Reveal and explain'):
        root=z[0,0];correct=root['net']>0
        if choice is not None:(st.success if (choice=='Begin / buy access')==correct else st.error)('Compare continuation with the initial cost, not merely with zero.')
        a,b,c=st.columns(3);a.metric('Before initial cost',f'{root["C"]:.4f}');b.metric('Starting NPV',f'{root["net"]:.4f}');c.metric('Option to start',f'{root["F"]:.4f}')
        st.html(tree_svg(m,costs,q,z,[],{},reveal=True))
        st.write('The starting NPV subtracts the initial cost once. At later gates that cost is sunk. Pale stop nodes show where paying would not add value.')
    st.caption('These are small variations, not detailed real-options case studies. All inputs are hypothetical.')


def practice():
    st.title('Interpretation practice')
    topic=st.selectbox('Topic',['All']+sorted({q[0] for q in QUESTIONS}),key='practice_topic')
    indices=[i for i,q in enumerate(QUESTIONS) if topic=='All' or q[0]==topic]
    i=st.selectbox('Question',indices,format_func=lambda i:f'{i+1}. {QUESTIONS[i][1]}',key='practice_question_'+topic)
    tag,prompt,options,correct,feedback=QUESTIONS[i]
    st.subheader(prompt);key=f'practice_{i}'
    answer=st.radio('Choose an answer',options,index=None,key=key+'_answer')
    a,b=st.columns(2)
    if a.button('Check answer',key=key+'_check'):
        if answer is None:st.info('Select an answer first.')
        else:
            j=options.index(answer);(st.success if j==correct else st.error)(feedback[j])
    b.button('Retry',key=key+'_retry',on_click=lambda:st.session_state.pop(key+'_answer',None))
    with st.expander('Hint'):
        st.write({'Pricing weights':'Separate forecasting from market-consistent valuation.','Growth factor':'R is a future dollar value over exactly one step.','Backward recursion':'Identify the claim being valued and the time interval.','Gates':'Separate signed NPV from the option to decline.','Economic meaning':'Ask what is still discretionary and what has already been paid.','Construction':'Keep contract dates separate from numerical time steps.'}[tag])
    with st.expander('Explain every answer'):
        for j,o in enumerate(options):st.markdown(f'**{o}** — {feedback[j]}')


if route=='home':
    st.title('Value the choice. Then make the decision.')
    st.write('A hands-on companion to **The Binomial Model: From option values to investment decisions**. Complete small lattices without getting buried in arithmetic.')
    a,b,c=st.columns(3);a.metric('Largest problem','4 periods');b.metric('Guided lattices','5');c.metric('Interpretation questions','16')
    st.subheader('How to use the studio')
    st.markdown('1. **Identify five inputs.** Multiple-choice answers reveal dt, u, d, R and p.\n2. **Click a lattice node.** Start at maturity and work from right to left.\n3. **Enter an expression.** Correct answers fill the cell; incorrect answers can be retried.\n4. **Choose how much to calculate.** In three- and four-period guided problems, solve one cell and optionally fill the rest of its column. A full worked lattice is always available.')
    st.info('A worked solution is always available. You are never locked out of a page because of an incorrect attempt.')
    st.subheader('The route')
    st.write('Build the lattice → one-period valuation → two-period recursion → compound options → three-period policy → four periods with only selected gates.')
    st.subheader('Read the colors')
    st.markdown('In clickable trees, **black** shows the underlying and **red V** shows the option value after any gate decision. **Blue** labels show payments. Pale green means continue; pale red means abandon. Decision labels accompany the colors. The small-experiments page also shows green net values and red values before payment.')
    st.write('A zero option value can hide a negative investment NPV. Gate feedback and worked solutions distinguish signed NPV from the option to decline.')
    st.subheader('Conventions')
    st.write('The lecture examples use 5% effective annual risk-free growth: R = 1.05 for a one-year step, equivalent to continuous r = ln(1.05). Their up/down returns are supplied directly and q = 0. The construction page uses CRR volatility calibration and permits a dividend/convenience yield q. Values are hypothetical monetary units. There are no technical failures or salvage proceeds. Stopping at a gate is permanent.')
    st.caption('Prerequisites: call payoff max(S − K, 0) and present value. This studio teaches binomial and compound-option reasoning, not a complete real-options valuation framework.')
elif route=='setup':setup()
elif route in CASES:lesson(route)
elif route=='applications':applications()
else:practice()
