package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.AbstractSul;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.config.SulConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.utils.CleanupTasks;

public class SulBuilderBLE implements SulBuilder<InputBLE, OutputBLE, ExecutionContextBLE> {
    @Override
    public AbstractSul<InputBLE, OutputBLE, ExecutionContextBLE> build(SulConfig sulConfig, CleanupTasks cleanupTasks) {
        return new SulBLE(sulConfig, cleanupTasks);
    }
}
