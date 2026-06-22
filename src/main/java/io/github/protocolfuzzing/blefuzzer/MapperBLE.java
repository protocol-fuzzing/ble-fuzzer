package io.github.protocolfuzzing.blefuzzer;

import io.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputBuilderBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputCheckerBLE;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.Mapper;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputChecker;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.config.MapperConfig;

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
