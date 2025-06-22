package com.github.protocolfuzzing.blefuzzer;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.AbstractSul;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulAdapter;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.config.SulConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.sulwrappers.DynamicPortProvider;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.Mapper;
import com.github.protocolfuzzing.protocolstatefuzzer.utils.CleanupTasks;

import jep.SharedInterpreter;

public class SulBLE implements AbstractSul<InputBLE, OutputBLE, ExecutionContextBLE> {
    private static final Logger LOGGER = LogManager.getLogger();
    protected MapperBLE dummyMapper;
    protected DynamicPortProvider dynamicPortProvider;
    protected SulServerConfigBLE config;
    protected CleanupTasks cleanupTasks;
    protected SharedInterpreter interp;

    public SulBLE(SulConfig sulConfig, CleanupTasks cleanupTasks) {
        this.dummyMapper = new MapperBLE();
        this.config = (SulServerConfigBLE) sulConfig;
        this.cleanupTasks = cleanupTasks;

        // Find the right mapper to use
        String mapper = "BLESUL";
        if(config.getMapper() != null) {
            mapper += "_" + config.getMapper();
        }
        
        // Set up the python interpreter for our mapper
        interp = new SharedInterpreter();
        interp.exec("import sys; sys.path.insert(0, 'py')");
        interp.exec(String.format("from %s import %s as SUL", mapper, mapper));
        interp.exec(String.format("b = SUL('%s', '%s')", config.getAdapterSerialPort(), config.getTargetMacAddr()));

        // Cleanup task to save the pcap and close the serial device
        cleanupTasks.submit(new Runnable() {
            @Override
            public void run() {
                LOGGER.debug("Closing serial port...");
                interp.exec("b.close()");
            }
        });
    }

    @Override
    public void pre() {
        LOGGER.debug("SulBLE: pre");
        interp.exec("b.pre()");
    }

    @Override
    public OutputBLE step(InputBLE in) {
        LOGGER.debug("SulBLE: step");
        interp.exec(String.format("outsym = b.step('%s')", in.getName()));
        String outputSymbol = (String) interp.getValue("outsym");
        return new OutputBLE(outputSymbol);
    }

    @Override
    public void post() {
        LOGGER.debug("SulBLE: post");
        interp.exec("b.post()");
    }


    @Override
    public SulConfig getSulConfig() {
        return config;
    }

    @Override
    public CleanupTasks getCleanupTasks() {
        return cleanupTasks;
    }

    @Override
    public void setDynamicPortProvider(DynamicPortProvider dynamicPortProvider) {
        this.dynamicPortProvider = dynamicPortProvider;
    }

    @Override
    public DynamicPortProvider getDynamicPortProvider() {
        return this.dynamicPortProvider;
    }

    @Override
    public Mapper<InputBLE, OutputBLE, ExecutionContextBLE> getMapper() {
        return this.dummyMapper;
    }

    @Override
    public SulAdapter getSulAdapter() {
        return null;
    }
}
