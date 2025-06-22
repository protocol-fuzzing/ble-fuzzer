package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.context.ExecutionContext;

public class ExecutionContextBLE implements ExecutionContext<InputBLE, OutputBLE, Object> {
    public ExecutionContextBLE() {}

    @Override
    public Object getState() {
        return null;
    }

    @Override
    public void disableExecution() {}

    @Override
    public void enableExecution() {}

    @Override
    public boolean isExecutionEnabled() {
        return true;
    }

    @Override
    public void setInput(InputBLE input) {}

    @Override
    public void setOutput(OutputBLE output) {}
}
