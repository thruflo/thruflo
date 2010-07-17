'define metadata';
({
    'description': 'thruflo syntax highlighter',
    'dependencies': { 
      'standard_syntax': '0.0.0'
    },
    'environments': { 
      'worker': true
    },
    'provides': [{
        'ep': 'syntax',
        'name': 'thruflo',
        'pointer': '#JSSyntax',
        'fileexts': [
          'md',
          'markdown',
          'thruflo'
        ]
      }, {
        'ep': 'themestyles',
        'url': [
          'thruflo.less',
          'global.less'
        ]
      }
    ]
  }
);
'end';

exports.someFunction = function() { };