"use strict";

function render(text) {
    var rendered = "";
    var color = "white";
    for (var i = 0; i < text.length; i++) {
        switch (text[i]) {
        case '\\':
            var prevColor = color;
            if (text[i + 1] === 'c') {
                color = text[i + 2];
            }
            if (color !== prevColor) {
                if (prevColor !== "white") {
                    rendered += "</span>";
                }
                if (color !== 'white') {
                    rendered += '<span class="' + color + '">';
                }
            }
            i += 2;
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
