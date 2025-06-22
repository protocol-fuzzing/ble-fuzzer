package com.github.protocolfuzzing.blefuzzer.symbols;

import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.abstractsymbols.OutputChecker;

public class OutputCheckerBLE implements OutputChecker<OutputBLE> {

    @Override
    public boolean hasInitialClientMessage(OutputBLE output) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'hasInitialClientMessage'");
    }

    @Override
    public boolean isTimeout(OutputBLE output) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'isTimeout'");
    }

    @Override
    public boolean isUnknown(OutputBLE output) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'isUnknown'");
    }

    @Override
    public boolean isSocketClosed(OutputBLE output) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'isSocketClosed'");
    }

    @Override
    public boolean isDisabled(OutputBLE output) {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'isDisabled'");
    }

}
