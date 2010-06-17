function (doc) {
  if (doc.namespace && doc.slug) {
    emit([
        doc.doc_type,
        doc.namespace,
        doc.slug,
        doc.mod
      ],
      null
    );
  }
}
