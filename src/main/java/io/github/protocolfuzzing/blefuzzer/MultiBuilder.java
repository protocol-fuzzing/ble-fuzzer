package io.github.protocolfuzzing.blefuzzer;

import io.github.protocolfuzzing.blefuzzer.symbols.AlphabetPojoXmlBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import io.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import io.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.AlphabetBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.AlphabetBuilderStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.xml.AlphabetSerializerXml;
import io.github.protocolfuzzing.protocolstatefuzzer.components.learner.config.LearnerConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.components.learner.statistics.MealyMachineWrapper;
import io.github.protocolfuzzing.protocolstatefuzzer.components.sul.core.SULBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzer;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerComposerStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.StateFuzzerStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerClientConfig;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerClientConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerConfigBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerEnabler;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerServerConfig;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.core.config.StateFuzzerServerConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.DiffTester;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.DiffTesterBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.DiffTesterEnabler;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.DiffTesterStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.config.DiffTesterConfig;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.config.DiffTesterConfigBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.difftester.config.DiffTesterConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunner;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunnerBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.TestRunnerStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.config.TestRunnerConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.core.config.TestRunnerEnabler;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbe;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbeBuilder;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.TimingProbeStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.config.TimingProbeConfigStandard;
import io.github.protocolfuzzing.protocolstatefuzzer.statefuzzer.testrunner.timingprobe.config.TimingProbeEnabler;

public class MultiBuilder implements
    StateFuzzerConfigBuilder,
    DiffTesterConfigBuilder,
    StateFuzzerBuilder<MealyMachineWrapper<InputBLE, OutputBLE>>,
    DiffTesterBuilder,
    TestRunnerBuilder,
    TimingProbeBuilder {

    protected AlphabetBuilder<InputBLE> alphabetBuilder = new AlphabetBuilderStandard<InputBLE>(
        new AlphabetSerializerXml<InputBLE, AlphabetPojoXmlBLE>(InputBLE.class, AlphabetPojoXmlBLE.class)
    );

    protected SULBuilder<InputBLE, OutputBLE, ExecutionContextBLE> sulBuilder = new SulBuilderBLE();

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
    public DiffTesterConfig buildConfig() {
        return new DiffTesterConfigStandard();
    }

    @Override
    public StateFuzzer<MealyMachineWrapper<InputBLE, OutputBLE>> build(StateFuzzerEnabler stateFuzzerEnabler) {
        return new StateFuzzerStandard<InputBLE, OutputBLE>(
            new StateFuzzerComposerStandard<InputBLE, OutputBLE, ExecutionContextBLE>(stateFuzzerEnabler, alphabetBuilder, sulBuilder).initialize()
        );
    }

    @Override
    public DiffTester build(DiffTesterEnabler diffTesterEnabler) {
        return new DiffTesterStandard<>(diffTesterEnabler, alphabetBuilder);
    }

    @Override
    public TestRunner build(TestRunnerEnabler testRunnerEnabler) {
        return new TestRunnerStandard<InputBLE, OutputBLE, Object, ExecutionContextBLE>(testRunnerEnabler, alphabetBuilder, sulBuilder).initialize();
    }

    @Override
    public TimingProbe build(TimingProbeEnabler timingProbeEnabler) {
        return new TimingProbeStandard<InputBLE, OutputBLE, Object, ExecutionContextBLE>(timingProbeEnabler, alphabetBuilder, sulBuilder).initialize();
    }
}
