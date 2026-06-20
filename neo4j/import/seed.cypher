// Substations
UNWIND range(1,10) AS sid
MERGE (s:Substation {id:'SEED-SUB-' + toString(sid)})
SET s.name='Seed Substation ' + toString(sid),
    s.district='District ' + toString(sid);

// Transformers
UNWIND range(1,40) AS tid
MATCH (s:Substation {
    id:'SEED-SUB-' + toString(((tid - 1) % 10) + 1)
})
MERGE (t:Transformer {id:'SEED-TX-' + toString(tid)})
SET t.name='Seed Transformer ' + toString(tid),
    t.capacity_kva=250 + tid * 10
MERGE (s)-[:FEEDS]->(t);

// Smart meters
UNWIND range(1,200) AS mid
MATCH (t:Transformer {
    id:'SEED-TX-' + toString(((mid - 1) % 40) + 1)
})
MERGE (m:SmartMeter {id:'SEED-SM-' + toString(mid)})
SET m.customer='Seed Consumer ' + toString(mid),
    m.status='ACTIVE'
MERGE (t)-[:SUPPLIES]->(m);
