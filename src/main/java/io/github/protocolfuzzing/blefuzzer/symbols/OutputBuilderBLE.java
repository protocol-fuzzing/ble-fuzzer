package io.github.protocolfuzzing.blefuzzer.symbols;

import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputBuilder;

public class OutputBuilderBLE extends OutputBuilder<OutputBLE> {

    @Override
    public OutputBLE buildOutputExact(String name) {
        return new OutputBLE(name);
    }

}
