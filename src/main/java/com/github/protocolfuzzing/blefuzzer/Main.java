package com.github.protocolfuzzing.blefuzzer;

import com.github.protocolfuzzing.blefuzzer.symbols.InputBLE;
import com.github.protocolfuzzing.blefuzzer.symbols.OutputBLE;
import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.statistics.MealyMachineWrapper;
import com.github.protocolfuzzing.protocolstatefuzzer.entrypoints.CommandLineParser;

public class Main {
    public static void main(String[] args) {
        // Multibuilder implements all necessary builders
        MultiBuilder mb = new MultiBuilder();

        // single parentLogger, if Main resides in the outermost package
        String[] parentLoggers = {Main.class.getPackageName()};

        CommandLineParser<MealyMachineWrapper<InputBLE, OutputBLE>> commandLineParser = new CommandLineParser<MealyMachineWrapper<InputBLE, OutputBLE>>(mb, mb, mb, mb);
        commandLineParser.setExternalParentLoggers(parentLoggers);

        commandLineParser.parse(args, true);
    }
}