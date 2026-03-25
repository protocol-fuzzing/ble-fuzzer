package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.AbstractSul;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulAdapter;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.config.SulConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.sulwrappers.DynamicPortProvider;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.mapper.Mapper;
import com.github.protocolfuzzing.protocolstatefuzzer.utils.CleanupTasks;
import jep.SharedInterpreter;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SulBLE implements AbstractSul<InputBLE, OutputBLE, ExecutionContextBLE> {
    private static final Logger LOGGER = LogManager.getLogger();
    private static boolean instanceCreated = false;
    protected MapperBLE dummyMapper;
    protected DynamicPortProvider dynamicPortProvider;
    protected SulServerConfigBLE config;
    protected CleanupTasks cleanupTasks;
    protected SharedInterpreter interp;
    protected ExecutorService interpThread = Executors.newSingleThreadExecutor();

    public SulBLE(SulConfig sulConfig, CleanupTasks cleanupTasks) {
        if (instanceCreated) {
            throw new IllegalStateException("Only a single instance of SulBLE can communicate with the target device. Make sure that -eqvThreads=1");
        }
        instanceCreated = true;

        this.dummyMapper = new MapperBLE();
        this.config = (SulServerConfigBLE) sulConfig;
        this.cleanupTasks = cleanupTasks;

        // Find the right mapper to use
        String mapper = config.getMapper() != null ? "BLESUL_" + config.getMapper() : "BLESUL";

        // Set up the python interpreter on a dedicated thread
        pythonThreadRun(() -> interp = new SharedInterpreter());
        pythonExec("import sys; sys.path.insert(0, 'py')");
        pythonExec(String.format("from %s import %s as SUL", mapper, mapper));
        pythonExec(String.format("b = SUL('%s', '%s')", config.getAdapterSerialPort(), config.getTargetMacAddr()));

        // Cleanup task to save the pcap and close the serial device
        cleanupTasks.submit(new Runnable() {
            @Override
            public void run() {
                LOGGER.debug("Closing serial port...");
                pythonExec("b.close()");
                interpThread.shutdown();
            }
        });
    }

    private <T> T pythonThreadRun(java.util.concurrent.Callable<T> task) {
        try {
            return interpThread.submit(task).get();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        } catch (ExecutionException e) {
            throw new RuntimeException(e.getCause());
        }
    }

    private void pythonThreadRun(Runnable task) {
        try {
            interpThread.submit(task).get();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        } catch (ExecutionException e) {
            throw new RuntimeException(e.getCause());
        }
    }

    protected void pythonExec(String s) {
        pythonThreadRun(() -> interp.exec(s));
    }

    protected String pythonEval(String s) {
        return pythonThreadRun(() -> {
            interp.exec(String.format("__jep_out = str(%s)", s));
            return (String) interp.getValue("__jep_out");
        });
    }

    @Override
    public void pre() {
        LOGGER.debug("SulBLE: pre");
        pythonExec("b.pre()");
    }

    @Override
    public OutputBLE step(InputBLE in) {
        LOGGER.debug("SulBLE: step");
        String outputSymbol = pythonEval(String.format("b.step('%s')", in.getName()));
        return new OutputBLE(outputSymbol);
    }

    @Override
    public void post() {
        LOGGER.debug("SulBLE: post");
        pythonExec("b.post()");
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
