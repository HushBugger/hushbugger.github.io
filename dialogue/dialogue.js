"use strict";

function render(text) {
    var rendered = "";
    var color = "white";
    for (var i = 0; i < text.length; i++) {
        switch (text[i]) {
        case '\\':
            var prevColor = color;
            switch (text[i + 1]) {
                // Text colors
            case 'W': case 'X': color = "white"; i += 1; break;
            case 'R': color = "red"; i += 1; break;
            case 'Y': color = "yellow"; i += 1; break;
            case 'L': color = "lightblue"; i += 1; break;
            case 'B': color = "blue"; i += 1; break;
            case 'G': color = "green"; i += 1; break;
            case 'O': color = "orange"; i += 1; break;
            case 'P': color = "purple"; i += 1; break;
            case 'C':
                // Probably something to do with dialogue options
                i += 1;
                break;
            case 'E': case 'F': case 'M': case 'T':
                // Facial expressions
                i += 2;
                break;
            case 'z':
                // Infinity symbol
                // Only appears as \z4, not sure what the 4 does
                rendered += '<img src="infty.png" alt="∞">';
                i += 5;
            }
            if (color !== prevColor) {
                if (prevColor !== "white") {
                    rendered += "</span>";
                }
                if (color !== 'white') {
                    rendered += '<span class="' + color + '">';
                }
            }
            break;
        case '/':
            if (text[i + 1] === '*') {
                i += 1;
            }
            break;
        case '&': case '#':
            // Line breaks
            rendered += '\n';
            break;
        case '^':
            // Speech pauses
            for (var j = 0; j < 10; j++) {
                if (text[i + 1] === String(j)) {
                    i += 1;
                    break;
                }
            }
            break;
        case '%':
            break;
        case '>':
            rendered += "&gt;";
            break;
        case '<':
            rendered += "&lt;";
            break;
        default:
            rendered += text[i];
        }
    }
    if (color !== "white") {
        rendered += "</span>";
    }
    return rendered;
}

function textbox(character, index) {
    var text = d[character][index];
    var box = document.createElement('div');
    box.classList.add('textbox');
    box.classList.add(character.startsWith("Papyrus") ? 'papyrus' :
                      character.startsWith("Sans") ? 'sans' :
                      'dtm');
    var link = document.createElement('a');
    link.href = '#' + character + ':' + index;
    link.classList.add('textbox');
    link.innerHTML = render(text);
    box.appendChild(link);
    return box;
}

function addBox(character, index) {
    document.getElementById('textboxes').appendChild(textbox(character, index));
}

function addBoxes(character) {
    for (var i = 0; i < d[character].length; i++) {
        addBox(character, i);
    }
}
