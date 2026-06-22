package io.github.protocolfuzzing.blefuzzer;

import io.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.AbstractSUL;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULWrapper;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULWrapperStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.config.SULConfig;
import io.github.protocolfuzzing.protocolstatefuzzer.utils.CleanupTasks;

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
