"""A small original insurance-policy knowledge base (written for this
project, not copied from any source), used by the example Claims FAQ agent."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document:
    doc_id: str
    title: str
    text: str


DOCUMENTS: list[Document] = [
    Document(
        "auto-liability",
        "Auto Liability Coverage",
        "Liability coverage on an auto policy pays for injuries or property damage the "
        "policyholder causes to someone else in an accident, up to the policy's limits. It does "
        "not pay for the policyholder's own vehicle damage or injuries, which fall under separate "
        "collision, comprehensive, or medical coverage.",
    ),
    Document(
        "auto-collision",
        "Collision and Comprehensive Coverage",
        "Collision coverage pays to repair or replace the policyholder's own vehicle after a "
        "crash, regardless of fault. Comprehensive coverage pays for damage from events other "
        "than a collision, such as theft, fire, falling objects, or hitting an animal. Both "
        "coverages are typically subject to a deductible the policyholder chooses when buying "
        "the policy.",
    ),
    Document(
        "home-dwelling",
        "Homeowners Dwelling Coverage",
        "Dwelling coverage on a homeowners policy pays to repair or rebuild the physical "
        "structure of the home after a covered loss such as fire or wind damage. The dwelling "
        "coverage limit should reflect the cost to rebuild the home, which is not always the "
        "same as its market value.",
    ),
    Document(
        "home-personal-property",
        "Personal Property Coverage",
        "Personal property coverage reimburses the policyholder for belongings inside the home, "
        "such as furniture and electronics, that are damaged, destroyed, or stolen in a covered "
        "loss. High value items like jewelry or fine art often have lower built in limits and may "
        "need a separate scheduled endorsement for full coverage.",
    ),
    Document(
        "claims-process",
        "The Claims Filing Process",
        "Filing a claim typically starts with reporting the loss to the insurer as soon as "
        "possible, after which a claims adjuster is assigned to investigate, estimate the damage, "
        "and determine what the policy covers. The policyholder should document the damage with "
        "photos and keep receipts for any temporary repairs or related expenses.",
    ),
    Document(
        "deductible-explained",
        "How a Deductible Works",
        "A deductible is the amount a policyholder pays out of pocket before insurance coverage "
        "pays the rest of a covered claim. Choosing a higher deductible usually lowers the "
        "premium, while a lower deductible raises it, since the insurer is taking on more of the "
        "early cost of a claim.",
    ),
    Document(
        "premium-factors",
        "What Affects an Insurance Premium",
        "An insurance premium is influenced by factors such as the policyholder's claims history, "
        "the coverage limits and deductible chosen, the insured property's location and age, and "
        "for auto policies, the driver's history and the vehicle's make and model. Insurers use "
        "these factors together to estimate the likelihood and cost of a future claim.",
    ),
    Document(
        "underwriting",
        "What Underwriting Does",
        "Underwriting is the process an insurer uses to evaluate the risk of insuring a person or "
        "property and to decide what coverage to offer and at what price. An underwriter reviews "
        "application details, prior claims, and other risk factors before a policy is issued or "
        "renewed.",
    ),
    Document(
        "umbrella-policy",
        "Umbrella Liability Policies",
        "An umbrella policy adds an extra layer of liability coverage on top of an auto or "
        "homeowners policy, covering large claims once the underlying policy's liability limit is "
        "used up. It is typically bought by policyholders who want protection against a lawsuit "
        "or judgment larger than their standard policy limits.",
    ),
    Document(
        "policy-renewal",
        "Policy Renewal and Non-Renewal",
        "Most home and auto policies renew automatically for another term unless the policyholder "
        "or the insurer cancels or declines to renew. An insurer may choose not to renew a policy "
        "for reasons such as a significant change in risk or a pattern of claims, and must "
        "typically notify the policyholder in advance.",
    ),
]

DOCUMENTS_BY_ID = {doc.doc_id: doc for doc in DOCUMENTS}
