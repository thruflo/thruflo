function (doc) {
  if (doc.doc_type == 'Repository') {
    var i, paths, branch;
    for (branch in doc.branch_paths) {
      paths = doc.branch_paths[branch];
      for (i = 0; i < paths.length; i++) {
        emit([doc.owner, doc.name, branch, paths[i]], null);
      }
    }
  }
}