package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBuilderBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputCheckerBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.Mapper;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputChecker;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.config.MapperConfig;

public class MapperBLE implements Mapper<InputBLE, OutputBLE, ExecutionContextBLE> {
    protected OutputBuilder<OutputBLE> outputBuilder = new OutputBuilderBLE();
    protected OutputChecker<OutputBLE> outputChecker = new OutputCheckerBLE();

    @Override
    public OutputBLE execute(InputBLE input, ExecutionContextBLE context) {
        throw new UnsupportedOperationException("Unimplemented method 'execute'");
    }

    @Override
    public MapperConfig getMapperConfig() {
        return null;
    }

    @Override
    public OutputBuilder<OutputBLE> getOutputBuilder() {
        return outputBuilder;
    }

    @Override
    public OutputChecker<OutputBLE> getOutputChecker() {
        return outputChecker;
    }
    
}
