package com.github.protocolfuzzing.blefuzzer.symbols;

import com.github.protocolfuzzing.blefuzzer.ExecutionContextBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.AbstractInputXml;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputChecker;

public class InputBLE extends AbstractInputXml<OutputBLE, Object, ExecutionContextBLE> {

    public InputBLE() {
        super();
    }

    public InputBLE(String name) {
        super(name);
    }

    @Override
    public void preSendUpdate(ExecutionContextBLE context) {}

    @Override
    public void postSendUpdate(ExecutionContextBLE context) {}

    @Override
    public void postReceiveUpdate(OutputBLE output, OutputChecker<OutputBLE> outputChecker, ExecutionContextBLE context) {}

    @Override
    public Object generateProtocolMessage(ExecutionContextBLE context) {
        throw new UnsupportedOperationException("Unimplemented method 'generateProtocolMessage'");
    }
    
}
