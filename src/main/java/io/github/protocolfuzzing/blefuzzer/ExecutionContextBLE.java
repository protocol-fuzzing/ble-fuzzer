package io.github.protocolfuzzing.blefuzzer;

import io.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.context.ExecutionContext;

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
