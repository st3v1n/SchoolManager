module.exports = {
  mode: 'jit',
  content: [
   './templates/**/*.html', 
   
   './test-templates/**/*.html', 
   './test-templates/**/*.js', 


   './core/**/*.html', 
   './exam_management/**/*.html', 
   './school_management/**/*.html', 
   './schoolmanager/**/*.html', 
    './partials/**/*.html',  
    './widgets/**/*.html',  
    './static/**/*.js',    
    './static/**/*.css',     
    // './**/*.py', 
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        'primary-light': 'var(--primary-light)',
        background: 'var(--background)',
        'text-color': 'var(--text-color)',
      },
      borderRadius: {
        DEFAULT: 'var(--border-radius)',
      },
      boxShadow: {
        DEFAULT: 'var(--shadow)',
      },
    },
  },
  plugins: [],
}
