package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.AlphabetPojoXmlBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.AlphabetBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.AlphabetBuilderStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.xml.AlphabetSerializerXml;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.config.LearnerConfigStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.statistics.MealyMachineWrapper;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulWrapper;
import com.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SulWrapperStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzer;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerComposerStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerClientConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerClientConfigStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerConfigBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerEnabler;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerServerConfig;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerServerConfigStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunner;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunnerBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunnerStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.config.TestRunnerConfigStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.config.TestRunnerEnabler;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbe;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbeBuilder;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbeStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.config.TimingProbeConfigStandard;
import com.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.config.TimingProbeEnabler;

public class MultiBuilder implements
    StateFuzzerConfigBuilder,
    StateFuzzerBuilder<MealyMachineWrapper<InputBLE, OutputBLE>>,
    TestRunnerBuilder,
    TimingProbeBuilder {

    protected AlphabetBuilder<InputBLE> alphabetBuilder = new AlphabetBuilderStandard<InputBLE>(
        new AlphabetSerializerXml<InputBLE, AlphabetPojoXmlBLE>(InputBLE.class, AlphabetPojoXmlBLE.class)
    );

    protected SulBuilder<InputBLE, OutputBLE, ExecutionContextBLE> sulBuilder = new SulBuilderBLE();
    protected SulWrapper<InputBLE, OutputBLE, ExecutionContextBLE> sulWrapper = new SulWrapperStandard<InputBLE, OutputBLE, ExecutionContextBLE>();

    @Override
    public StateFuzzerClientConfig buildClientConfig() {
        return new StateFuzzerClientConfigStandard(null, null, null, null);
    }

    @Override
    public StateFuzzerServerConfig buildServerConfig() {
        return new StateFuzzerServerConfigStandard(
            new LearnerConfigStandard(),
            new SulServerConfigBLE(),
            new TestRunnerConfigStandard(),
            new TimingProbeConfigStandard()
        );
    }

    @Override
    public StateFuzzer<MealyMachineWrapper<InputBLE, OutputBLE>> build(StateFuzzerEnabler stateFuzzerEnabler) {
        return new StateFuzzerStandard<InputBLE, OutputBLE>(
            new StateFuzzerComposerStandard<InputBLE, OutputBLE, ExecutionContextBLE>(stateFuzzerEnabler, alphabetBuilder, sulBuilder, sulWrapper).initialize()
        );
    }

    @Override
    public TestRunner build(TestRunnerEnabler testRunnerEnabler) {
        return new TestRunnerStandard<InputBLE, OutputBLE, Object, ExecutionContextBLE>(testRunnerEnabler, alphabetBuilder, sulBuilder, sulWrapper).initialize();
    }

    @Override
    public TimingProbe build(TimingProbeEnabler timingProbeEnabler) {
        return new TimingProbeStandard<InputBLE, OutputBLE, Object, ExecutionContextBLE>(timingProbeEnabler, alphabetBuilder, sulBuilder, sulWrapper).initialize();
    }
}