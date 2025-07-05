class Editor {
    constructor(editorId) {
        this.editor = document.getElementById(editorId);
        this.questions = [];
        this.debounceTimer = null;
        this.AUTO_SAVE_INTERVAL = 100000;
        this.init();

        if (questions.length > 0) {
            questions.forEach(q => this.loadQuestion(q));
        } else {
            this.createQuestionBox();   
        }
    }

    init() {
        this.setupGlobalListeners();
    }

    loadQuestion(questionData) {
        const questionId = questionData.id || Date.now().toString();
        const qbox = this.questionTemplate(questionId);
        this.editor.insertAdjacentHTML('beforeend', qbox);

        const questionEl = this.editor.querySelector(`[data-question-id="${questionId}"]`);

        // Populate question content
        questionEl.querySelector('.question-content').innerHTML = questionData.content;

        // Populate question type
        questionEl.querySelector('.question-type').value = questionData.type;

        // Populate marks
        // questionEl.querySelector('.marks-input').value = questionData.marks;

        // Populate options
        const optionsContainer = questionEl.querySelector('.optioncontainer');
        questionData.options.forEach(opt => {
            this.addOption(optionsContainer);
            const lastOption = optionsContainer.lastElementChild;
            lastOption.querySelector('div[contenteditable]').innerHTML = opt.text;
            lastOption.querySelector('input[type="radio"]').checked = opt.correct;
        });

        // Set up listeners for the new question
        this.setupQuestionListeners(questionId);
        this.questions.push(questionId);
    }

    createQuestionBox() {
        const questionId = Date.now().toString();
        const qbox = this.questionTemplate(questionId);
        this.editor.insertAdjacentHTML('beforeend', qbox);
        this.setupQuestionListeners(questionId);
        this.questions.push(questionId);
    }

    questionTemplate(id) {
        return `
            <div data-question-id="${id}" class="questionbox group max-w-4xl mx-auto border border-gray-200 bg-white rounded-lg m-2 shadow-sm hover:shadow-md transition-shadow">
                <div class="question-header p-2 bg-gray-100 border-b">Question</div>
                ${this.toolbarTemplate()}
                <div class="p-4 min-h-[150px] focus:outline-none question-content" contenteditable="true" data-placeholder="Start typing your question..."></div>
                ${this.footerTemplate()}
                <div class="error-container p-2"></div> <!-- Error container -->
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
                <option value="multiple_choice">Multiple Choice</option>
                <option disabled value="fib">Fill in</option>
            </select>
        `;
    }

    formattingTools() {
        return `
            <div>
                <button data-command="bold" class="editor-tool" title="Bold">B</button>
                <button data-command="italic" class="editor-tool" title="Italic">I</button>
                <button data-command="underline" class="editor-tool" title="Underline">U</button>
                <span class="divider"></span>
                <button data-command="insertUnorderedList" class="editor-tool" title="Bullet List">•</button>
                <button data-command="insertOrderedList" class="editor-tool" title="Numbered List">1.</button>
            </div>
        `;
    }

    insertTools() {
        return `
            <div>
                <button data-action="insertImage" class="editor-tool" title="Insert Image">📷</button>
                <button data-action="insertTable" class="editor-tool" title="Insert Table">🗂️</button>
                <button data-action="insertMath" class="editor-tool" title="Insert Math Equation">Σ</button>
                <input type="file" class="hidden" accept="image/*" data-action="insertImageFile">
            </div>
        `;
    }

    
    footerTemplate() {
        //removed this cus total score will now be calculated  using no of correct/no of questions * total_score for exam Mark:<input type="number" min="1" value="1" class="marks-input w-16 px-2 py-1 border rounded" title="Marks for this question">
        return `
            <div class="question-footer border-t p-2 bg-gray-50">
                <div class="optioncontainer"></div>    
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
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

        // questionEl.querySelector('.question-content').addEventListener('input', () => {
        //     this.handleContentChange(id);
        // });

        // questionEl.querySelector('.marks-input').addEventListener('input', () => {
        //     this.handleContentChange(id);
        // });
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
        
        // newQuestionEl.querySelector('.marks-input').value = 
        //     originalQuestion.querySelector('.marks-input').value;
        
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

    sanitizeHTML(content) {
        const temp = document.createElement('div');
        temp.textContent = content;
        return temp.innerHTML;
    }

    insertMathEquation(questionEl) {
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

    // handleContentChange(questionId) {
    //     clearTimeout(this.debounceTimer);
    //     this.debounceTimer = setTimeout(() => {
    //         this.saveQuestion(questionId);
    //     }, this.AUTO_SAVE_INTERVAL);
    // }

    // handle editing and creating questions
    // async saveQuestion(questionId) {
    //     const questionData = this.getQuestionData(questionId);
    //     const csrftoken = getCookie('csrftoken')
    //     try {
    //         const response = await fetch(`/exam/save_question/${exam_id}/`, {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json',
    //                 'X-CSRFToken': csrftoken
    //             },
    //             body: JSON.stringify({
    //                 ...questionData,
    //                 is_draft: true
    //             })
    //         });
    //         if (!response.ok) throw new Error('Save failed');
    //     } catch (error) {
    //         console.error('Auto-save failed:', error);
    //     }
    //     console.log(questionData)
    // }

    getQuestionData(questionId) {
        const questionEl = this.editor.querySelector(`[data-question-id="${questionId}"]`);
        return {
            id: questionId,
            type: questionEl.querySelector('.question-type').value,
            content: questionEl.querySelector('.question-content').innerHTML,
            // marks: parseInt(questionEl.querySelector('.marks-input').value) || 1,
            options: Array.from(questionEl.querySelectorAll('.optioncontainer .option-item')).map(opt => ({
                text: opt.querySelector('div[contenteditable]').innerHTML,
                correct: opt.querySelector('input[type="radio"]').checked
            })),
            mathEquations: Array.from(questionEl.querySelectorAll('.math-latex')).map(input => input.value),
            images: Array.from(questionEl.querySelectorAll('img')).map(img => img.src)
        };
    }

    getAllQuestions() {
        return this.questions.map(id => this.getQuestionData(id));
    }

}


// const editor = new Editor('editorContainer');