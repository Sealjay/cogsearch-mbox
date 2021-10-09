

using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using System;
using System.Text.Json.Serialization;

namespace webapp.Models
{
public partial class EmailRecord
{
    [SimpleField(IsFilterable = true, IsKey = true)]
    public string MessageId { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public string MessageSubject { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsSortable = true)]
    public string MessageFrom { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public string MessageTo { get; set; }

    [SearchableField()]
    public string MessageContent { get; set; }

    [SearchableField(IsFilterable = true, IsSortable = true, IsFacetable = true)]
    public string MessageDate { get; set; }

}
}