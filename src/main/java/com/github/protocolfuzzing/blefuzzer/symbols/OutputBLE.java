package com.github.protocolfuzzing.blefuzzer.symbols;

import java.util.Collections;

import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.AbstractOutput;

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
