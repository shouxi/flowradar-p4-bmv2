FlowRadar (bmv2)
========

FlowRader-P4 upgraded for bmv2.

P4 code: https://github.com/USC-NSL/FlowRadar-P4/tree/master/targets/simple_router/p4src
Involved hash functions: https://github.com/USC-NSL/p4c-behavioral/blob/master/p4c_bm/templates/src/checksums_algos.h#L241

## Install P4 simulator and compiler

Download and install [bmv2]() and [p4c-bmv2]().


## Build a target for FlowRadar-P4

    git clone github.com/shouxi/flowradar-p4-bmv2.git flowradar-p4-bmv2
    cd flowradar-p4-bmv2

    python create_target_for_flowradar.py

## Test FlowRadar-P4

Run Mininet:

    sh ./run_flowradar_demo.sh

Read counter values:

    python read_counters.py
