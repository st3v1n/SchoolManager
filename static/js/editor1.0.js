// ToDo: Add Question validators when you want to submit

class Editor {
    constructor(editorId) {
        this.debounceTimer = null;
        this.AUTO_SAVE_INTERVAL = 3000;
        this.editor = document.getElementById(editorId);
        this.questions = [];
        this.init();
    }

    init() {
        this.createQuestionBox();
        this.setupGlobalListeners();
    }


    createQuestionBox() {
        const questionId = Date.now().toString();
        const qbox = this.questionTemplate(questionId);
        this.editor.insertAdjacentHTML('beforeend', qbox);
        this.setupQuestionListeners(questionId);
        this.questions.push(questionId);
    }

    handleContentChange(questionId) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            if (this.validateQuestion(questionId).length === 0) {
            this.saveQuestion(questionId);
            }
        }, this.AUTO_SAVE_INTERVAL);
    }
    
    async saveQuestion(questionId) {
        const questionData = this.getQuestionData(questionId);
        try {
            const response = await fetch('/save-question/', {
            method: 'POST',
            body: JSON.stringify(questionData)
            });
            // Handle response
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }

    questionTemplate(id) {
        return `
            <div data-question-id="${id}" class="questionbox group max-w-4xl mx-auto border border-gray-200 bg-white rounded-lg m-2 shadow-sm hover:shadow-md transition-shadow">
                <div class="question-header p-2 bg-gray-100 border-b">Question</div>
                ${this.toolbarTemplate()}
                <div class="p-4 min-h-[150px] focus:outline-none question-content" contenteditable="true" data-placeholder="Start typing your question..."></div>
                ${this.footerTemplate()}
            </div>
        `;
    } 

    toolbarTemplate() {
        return `
            <div class="toolbar-container border-b p-2 bg-gray-50 hidden">
                <div class="flex items-center justify-between flex-wrap gap-2">
                    ${this.questionTypeSelector()}
                    ${this.formattingTools()}
                    ${this.insertTools()}
                </div>
            </div>
        `;
    }

    questionTypeSelector() {
        return `
            <select class="border rounded px-2 py-1 text-sm question-type">
                <option value="mcq">Multiple Choice</option>
                <option disabled value="fib">Fill in</option>
            </select>
        `;
    }

    formattingTools() {
        return `
            <div>
                <button data-command="bold" class="editor-tool" title="Bold"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bold"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"></path></svg></button>
                <button data-command="italic" class="editor-tool" title="Italic"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-italic"><line x1="19" y1="4" x2="10" y2="4"></line><line x1="14" y1="20" x2="5" y2="20"></line><line x1="15" y1="4" x2="9" y2="20"></line></svg></button>
                <button data-command="underline" class="editor-tool" title="Underline"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-underline"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"></path><line x1="4" y1="21" x2="20" y2="21"></line></svg></button>
                <span class="divider"></span>
                <button data-command="insertUnorderedList" class="editor-tool" title="Bullet List"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg></button>
                <button data-command="insertOrderedList" class="editor-tool" title="Numbered List">
                   <svg fill="#000000" viewBox="0 0 381.304 381.304" xml:space="preserve"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g> <path d="M121.203,37.858c0-7.791,6.319-14.103,14.104-14.103H367.2c7.784,0,14.104,6.312,14.104,14.103 s-6.312,14.103-14.104,14.103H135.307C127.522,51.961,121.203,45.649,121.203,37.858z M135.307,120.908h150.426 c7.79,0,14.104-6.315,14.104-14.104c0-7.79-6.313-14.103-14.104-14.103H135.307c-7.785,0-14.104,6.307-14.104,14.103 C121.203,114.598,127.522,120.908,135.307,120.908z M367.2,269.75H135.307c-7.785,0-14.104,6.312-14.104,14.104 c0,7.79,6.319,14.103,14.104,14.103H367.2c7.784,0,14.104-6.312,14.104-14.103C381.304,276.062,374.984,269.75,367.2,269.75z M285.727,338.693h-150.42c-7.785,0-14.104,6.307-14.104,14.104c0,7.79,6.319,14.103,14.104,14.103h150.426 c7.79,0,14.104-6.312,14.104-14.103C299.836,345.005,293.517,338.693,285.727,338.693z M33.866,127.838h22.387V14.405H37.921 c-0.521,5.925-0.068,10.689-4.696,14.277c-4.631,3.591-14.363,5.382-23.158,5.382H6.871v15.681h26.995V127.838z M25.603,345.147 l28.115-20.912c9.69-6.655,16.056-12.826,19.109-18.524c3.05-5.697,4.569-11.821,4.569-18.377c0-10.716-3.585-19.357-10.737-25.941 c-7.161-6.579-16.568-9.865-28.23-9.865c-11.245,0-20.241,3.328-26.982,9.989c-6.75,6.655-10.113,16.691-10.113,30.115H23.02 c0-8.015,1.416-13.548,4.253-16.621c2.834-3.067,6.721-4.604,11.665-4.604s8.854,1.561,11.741,4.676 c2.888,3.12,4.327,6.998,4.327,11.632c0,4.628-1.336,8.808-4.02,12.555c-2.675,3.747-10.125,10.071-22.352,18.962 c-10.453,7.648-24.154,16.964-28.393,23.726L0,364.96h77.632v-19.813H25.603L25.603,345.147z"></path> </g> </g></svg>
                </button>
            </div>
        `;
    }

    insertTools() {
        return `
            <div>
                <button data-action="insertImage" class="editor-tool" title="Insert Image">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-image"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                </button>
                <button data-action="insertTable" class="editor-tool" title="Insert Table">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-table"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"></path></svg>
                </button>
                <button data-action="insertMath" class="editor-tool" title="Insert Math Equation">
                <input type="file" class="hidden" accept="image/*" data-action="insertImageFile">
                    <svg fill="#000000" height="23" width="23" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 486.1 486.1" xml:space="preserve"><g><g><path d="M445.5,0H40.7C18.3,0,0,18.3,0,40.7v404.7c0,22.4,18.3,40.7,40.7,40.7h404.7c22.4,0,40.7-18.3,40.7-40.7V40.7C486.2,18.3,467.9,0,445.5,0z M462.2,445.5c0,9.2-7.5,16.7-16.7,16.7H40.7c-9.2,0-16.7-7.5-16.7-16.7V40.7C24,31.5,31.5,24,40.7,24h404.7c9.2,0,16.7,7.5,16.7,16.7v404.8H462.2z"/><path d="M193,300.6c-4.7-4.7-12.3-4.7-17,0l-36.1,36.1l-36.1-36.1c-4.7-4.7-12.3-4.7-17,0s-4.7,12.3,0,17l36.1,36.1l-36.1,36.1c-4.7,4.7-4.7,12.3,0,17c2.3,2.3,5.4,3.5,8.5,3.5c3.1,0,6.1-1.2,8.5-3.5l36.1-36.1l36.1,36.1c2.3,2.3,5.4,3.5,8.5,3.5s6.1-1.2,8.5-3.5c4.7-4.7,4.7-12.3,0-17l-36.1-36.1l36.1-36.1C197.7,312.9,197.7,305.3,193,300.6z"/><path d="M203,131.7h-51v-51c0-6.6-5.4-12-12-12s-12,5.4-12,12v51H77c-6.6,0-12,5.4-12,12s5.4,12,12,12h51v51c0,6.6,5.4,12,12,12s12-5.4,12-12v-51h51c6.6,0,12-5.4,12-12S209.6,131.7,203,131.7z"/><path d="M403.9,371.1H296.4c-6.6,0-12,5.4-12,12s5.4,12,12,12h107.4c6.6,0,12-5.4,12-12S410.5,371.1,403.9,371.1z"/><path d="M403.9,312.2H296.4c-6.6,0-12,5.4-12,12s5.4,12,12,12h107.4c6.6,0,12-5.4,12-12S410.5,312.2,403.9,312.2z"/><path d="M394.6,155.7c6.6,0,12-5.4,12-12s-5.4-12-12-12H287.1c-6.6,0-12,5.4-12,12s5.4,12,12,12H394.6z"/></g></g></svg>
                </button>
            </div>
        `;
    }

    footerTemplate() {
        return `
            <div class="question-footer border-t p-2 bg-gray-50">
                <div class="optioncontainer"></div>    
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <input type="number" min="1" value="1" 
                               class="marks-input w-16 px-2 py-1 border rounded" 
                               title="Marks for this question">
                        <button data-action="addOption" class="text-sm text-blue-600 hover:text-blue-800">
                            + Add Option
                        </button>
                    </div>
                    <div class="flex items-center gap-2">
                        <button data-action="duplicate" class="text-gray-500 hover:text-gray-700">
                            ⎘ Duplicate
                        </button>
                        <button data-action="delete" class="text-red-500 hover:text-red-700">
                            ⨉ Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    setupGlobalListeners() {
        this.editor.addEventListener('click', (e) => {
            const questionBox = e.target.closest('.questionbox');
            if (questionBox) this.toggleToolBar(questionBox);
        });

        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                const commands = { 'b': 'bold', 'i': 'italic', 'u': 'underline', 'n': 'newquestion' };
                if (commands[e.key]) {
                    e.preventDefault();
                    this.execCommand(commands[e.key]);
                }
            }
        });
    }

    setupQuestionListeners(id) {
        const questionEl = this.editor.querySelector(`[data-question-id="${id}"]`);

        questionEl.querySelectorAll('[data-command]').forEach(btn => {
            btn.addEventListener('click', () => this.execCommand(btn.dataset.command));
        });

        questionEl.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleAction(btn.dataset.action, id, e));
        });

        questionEl.querySelector('.question-content').addEventListener('input', () => {
            this.handleContentChange(id);
        });


        questionEl.querySelectorAll('input, select, .question-content').forEach(element => {
            element.addEventListener('input', () => this.handleContentChange(id));
        });

        this.editor.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="delete"]')) {
              this.handleDelete(e.target.closest('.questionbox'));
            }
        });
    }

    handleAction(action, questionId, event) {
        const questionEl = this.editor.querySelector(`[data-question-id="${questionId}"]`);

        switch (action) {
            case 'insertMath':
                this.insertMathEquation(questionEl);
                break;
            case 'insertImage':
                questionEl.querySelector('[data-action="insertImageFile"]').click();
                break;
                
            case 'insertImageFile':
                this.handleImageUpload(questionEl, event.target.files[0]);
                break;
                
            case 'insertTable':
                this.insertTable(questionEl);
                break;
                
            case 'addOption':
                this.addOption(questionEl.querySelector('.optioncontainer'));
                break;
                
            case 'duplicate':
                this.duplicateQuestion(questionId);
                break;
                
            case 'delete':
                this.deleteQuestion(questionId);
                break;
        }
    }

    sanitizeHTML(content) {
        const temp = document.createElement('div');
        temp.textContent = content;
        return temp.innerHTML;
    }

    insertMathEquation(questionEl) {
        // Add hidden input to store LaTeX
        const latexInput = document.createElement('input');
        latexInput.type = 'hidden';
        latexInput.className = 'math-latex';
        
        const updateLatexValue = () => {
            latexInput.value = mathf.latex();
        };

        // Modify MathQuill config
        const mathf = MQ.MathField(mathField, {
            handlers: {
            edit: () => {
                updateLatexValue();
                this.handleContentChange(questionId);
            }
            }
        });
    }

        
    async handleImageUpload(questionEl, file) {
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'max-w-full h-auto my-2 rounded';
            questionEl.querySelector('.question-content').appendChild(img);
        };
        reader.readAsDataURL(file);
    }

    insertTable(questionEl) {
        try {
            const rows = parseInt(prompt('Number of rows:', 2), 10) || 2;
            const cols = parseInt(prompt('Number of columns:', 2), 10) || 2;
            
            const table = document.createElement('table');
            table.className = 'border-collapse w-full my-2';
            
            for (let i = 0; i < rows; i++) {
                const tr = table.insertRow();
                for (let j = 0; j < cols; j++) {
                    const td = tr.insertCell();
                    td.className = 'border p-2';
                    td.contentEditable = true;
                    td.textContent = `Cell ${i+1},${j+1}`;
                }
            }
            questionEl.querySelector('.question-content').appendChild(table);
        } catch (error) {
            console.error('Error inserting table:', error);
        }
    }

    addOption(optionsContainer) {
        const questionId = optionsContainer.closest('[data-question-id]').dataset.questionId;
        const optionWrapper = document.createElement('div');
        optionWrapper.className = 'option-item flex items-center mb-2';

        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = `options-${questionId}`; 

        const optionContent = document.createElement('div');
        optionContent.contentEditable = true;
        optionContent.className = 'flex-grow border p-1';
        optionContent.setAttribute('data-placeholder', 'Option text');

        const deleteOptionBtn = document.createElement('button');
        deleteOptionBtn.textContent = '✕';
        deleteOptionBtn.className = 'ml-2 text-red-500';
        deleteOptionBtn.addEventListener('click', () => optionWrapper.remove());

        optionWrapper.appendChild(radioInput);
        optionWrapper.appendChild(optionContent);
        optionWrapper.appendChild(deleteOptionBtn);

        optionsContainer.appendChild(optionWrapper);
        optionContent.focus();
    }


    toggleToolBar(questionBox) {
        const toolbars = this.editor.querySelectorAll('.toolbar-container');
        toolbars.forEach(t => t.classList.add('hidden'));
        
        const currentToolbar = questionBox.querySelector('.toolbar-container');
        currentToolbar.classList.toggle('hidden');
    }

    duplicateQuestion(questionId) {
        const originalQuestion = this.editor.querySelector(`[data-question-id="${questionId}"]`);
        const newQuestionId = Date.now().toString();
        const newQuestionHTML = this.questionTemplate(newQuestionId);
        originalQuestion.insertAdjacentHTML('afterend', newQuestionHTML);
        
        const newQuestionEl = this.editor.querySelector(`[data-question-id="${newQuestionId}"]`);
        newQuestionEl.querySelector('.question-content').innerHTML = 
            originalQuestion.querySelector('.question-content').innerHTML;
        
        newQuestionEl.querySelector('.question-type').value = 
            originalQuestion.querySelector('.question-type').value;
        
        newQuestionEl.querySelector('.marks-input').value = 
            originalQuestion.querySelector('.marks-input').value;
        
        this.setupQuestionListeners(newQuestionId);
        this.questions.push(newQuestionId);
    }

    deleteQuestion(questionId) {
        const questionEl = this.editor.querySelector(`[data-question-id="${questionId}"]`);
        
        if (this.questions.length > 1) {
            questionEl.remove();
            this.questions = this.questions.filter(id => id !== questionId);
        } else {
            alert('Cannot delete the last question. Add a new question first.');
        }
    }

    handleContentChange(questionId) {
        const questionContent = this.editor.querySelector(`[data-question-id="${questionId}"] .question-content`);
        // enable monitoring if any part of the question change mainly to implement the optimized question gathering of changes
    }

    getQuestionData(questionId) {
        const questionEl = this.editor.querySelector(`[data-question-id="${questionId}"]`);
        return {
           
            // mathEquations: Array.from(questionEl.querySelectorAll('.math-latex'))
            // .map(input => input.value),
            // images: Array.from(questionEl.querySelectorAll('img'))
            // .map(img => img.src),
            // validation: this.validateQuestion(questionId)
        
            type: questionEl.querySelector('.question-type').value,
            content: questionEl.querySelector('.question-content').innerHTML,
            marks: questionEl.querySelector('.marks-input').value,
            options: Array.from(questionEl.querySelectorAll('.optioncontainer input[type="radio"]'))
                .map(opt => ({
                    text: opt.nextElementSibling.innerHTML,
                    correct: opt.checked
                }))
        };
    }

    getAllQuestions() {
        return this.questions.map(id => this.getQuestionData(id));
    }

    execCommand(command) {
        document.execCommand(command, false, null);
    }

    createElement(tag,  options = {} /*attr = {}*/, to, children = {}) {
        const el = document.createElement(tag);
        Object.entries(options).forEach(([key, value]) => {
            if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    el.dataset[dataKey] = dataValue;
                });
            } else if (key === 'textContent') {
                el.textContent = value;
            } else if (key === 'innerHtml') {
                el.innerHTML = value;
            } else if (key === 'onclick') {
                el.addEventListener('click', value);
            } else {
                el.setAttribute(key, options[key])
            }
        });
        to ? to.appendChild(el) : null;
        Object.entries(children).forEach(([key, value]) => {
            el.appendChild(value);
        });

        return el;
    }

}


const editor = new Editor('editorContainer');
var MQ = MathQuill.getInterface(2);



    {/* insertMathEquation(questionEl) {
        const questionContent = questionEl.querySelector('.question-content');
        
        const mathContainer = document.createElement('span');
        mathContainer.className = 'math-container';
        const mathField = document.createElement('span');
        mathField.className = 'mq-editable-field';
        mathContainer.appendChild(mathField);
    
        const spaceNode = document.createTextNode('\u200B');
        
        const wrapper = document.createElement('span');
        wrapper.className = 'math-wrapper';
        wrapper.appendChild(mathContainer);
        wrapper.appendChild(spaceNode);
        
        questionContent.appendChild(wrapper);
    
        var MQ = MathQuill.getInterface(2);
        const mathf = MQ.MathField(mathField, {
            handlers: {
                edit: () => {
                    //handle math field changes
                },
                enter: () => {
                    wrapper.focus();
                    const selection = window.getSelection();
                    const range = document.createRange();
                    range.setStartAfter(wrapper);
                    range.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }
        });
        mathf.focus()
    
        mathf.addEventListener('click', (e) => {
            e.stopPropagation();
            mathQuillField.focus();
        });

    } */}