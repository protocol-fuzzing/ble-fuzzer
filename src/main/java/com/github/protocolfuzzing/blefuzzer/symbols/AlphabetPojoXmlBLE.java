package com.github.protocolfuzzing.blefuzzer.symbols;

import com.github.protocolfuzzing.protocolstatefuzzer.components.learner.alphabet.xml.AlphabetPojoXml;
import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlElements;
import jakarta.xml.bind.annotation.XmlRootElement;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@XmlRootElement(name = "alphabet")
@XmlAccessorType(XmlAccessType.FIELD)
public class AlphabetPojoXmlBLE extends AlphabetPojoXml<InputBLE> {
    @XmlElements(value = {
        @XmlElement(type = InputPojoXmlBLE.class, name = "InputBLE")
    })
    private List<InputPojoXmlBLE> xmlInputs;

    public AlphabetPojoXmlBLE() {
        xmlInputs = new ArrayList<>();
    }

    public List<InputBLE> getInputs() {
        List<InputBLE> allInputs = xmlInputs.stream().map(xmlInput -> new InputBLE(xmlInput.name)).collect(Collectors.toList());
        return allInputs;
    }

    public static class InputPojoXmlBLE {
        @XmlAttribute(name = "name", required = true)
        private String name;
    }
}