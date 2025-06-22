package com.github.protocolfuzzing.blefuzzer.symbols;

import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputBuilder;

public class OutputBuilderBLE extends OutputBuilder<OutputBLE> {

    @Override
    public OutputBLE buildOutputExact(String name) {
        return new OutputBLE(name);
    }

}
