package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.AbstractSUL;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULWrapper;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULWrapperStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.config.SULConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.utils.CleanupTasks;

public class SulBuilderBLE implements SULBuilder<InputBLE, OutputBLE, ExecutionContextBLE> {
    @Override
    public AbstractSUL<InputBLE, OutputBLE, ExecutionContextBLE> buildSUL(SULConfig sulConfig, CleanupTasks cleanupTasks) {
        return new SulBLE(sulConfig, cleanupTasks);
    }

    @Override
    public SULWrapper<InputBLE,OutputBLE, ExecutionContextBLE> buildWrapper() {
        return new SULWrapperStandard<>();
    }
}
