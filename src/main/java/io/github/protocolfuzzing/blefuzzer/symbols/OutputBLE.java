package io.github.protocolfuzzing.blefuzzer.symbols;

import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.AbstractOutput;

import java.util.Collections;

public class OutputBLE extends AbstractOutput<OutputBLE, Object> {
    public OutputBLE(String name) {
        super(name);
        this.messages = Collections.emptyList();
    }

    @Override
    protected OutputBLE buildOutput(String name) {
        return new OutputBLE(name);
    }

    @Override
    protected OutputBLE convertOutput() {
        return this;
    }

}
