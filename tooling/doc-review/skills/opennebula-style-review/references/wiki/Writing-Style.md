### Tone and Voice

> [!NOTE]
>This section provides guidelines, not hard-and-fast rules. These guidelines do not work in all cases; depart from them if doing so improves your document.

Employ a tone that is friendly and informal, but not banal.

Try to use short, direct sentences, but avoid a dry tone. Using transitions and qualifiers (such as *though*, *however*, *moreover*) often helps.

Try to use simple words with a clear meaning. Don’t worry if a sentence doesn’t sound important enough; in fact, that is often a good sign.

When possible, address the reader in the second person, i.e. as *you*; avoid using the third person. For example, try to avoid: “This configuration allows users to...” Use instead: “This configuration allows you to...”

However, when introducing tutorials, it’s often recommended to use the first person plural, *we.* This helps to provide the reader with a sense of guidance. For example: “In this tutorial, we’ll deploy an OpenNebula Front-end on AWS.”

#### Active Voice vs. Passive Voice

In most cases it’s best to use *active voice*. In active voice, the person or entity performing the action is always identified; it is the subject of the sentence. For example: “The VMs in the service report `READY` to OneGate.” In passive voice, the action performed is the subject of the sentence, e.g. “The `READY` state is reported by the VMs to OneGate.” This second example is less direct and more likely to cause confusion.

However, In some cases the use of passive voice may be beneficial, such as when you want to emphasize the action over the agent. This may be the case if it doesn’t matter who performs the action, as in “Information is transferred over SSH.”

Whenever possible, try to use action verbs over linking verbs. An active verb specifies an action performed by the subject of the sentence; a linking verb describes the *state* of the subject of the sentence.

| Linking verbs | Action verbs |
| :---- | :---- |
| This page is a guide for installing... | This page describes how to install... |
| The Front-end is the management platform for the hypervisor nodes... | The Front-end manages the hypervisor nodes… |
| Below is a table with the options for... | The table below lists the options for...

#### Choosing Titles for Headings or Sections

Titles of headings or sections often help the reader to determine the type of content the section contains, for example instructions or reference.

If the document is a tutorial, consider hinting at the content of a section by using a gerund (i.e. a verb conjugated to end in *ing*), e.g.:

* Provisioning an Edge Cluster  
* Instantiating the VM Template  
* Connecting to the VM  
* Verifying the Installation

This form hints that the section provides instructions and additional information needed to achieve a partial goal, instead of explanation or reference.

#### Using the Imperative Mood

In English, the imperative mood is used to give instructions, for example:

> Enter your username and password, then click **Enter**.

In imperative mood, it’s usual to address the reader directly, as *you* (see [Tone and Voice](#tone-and-voice) above). For example:

> In this screen you can give your service a name, and specify the number of instances to create.

If an instructional sentence mentions the goal of the instruction, try to place it at the beginning of the sentence, e.g. “To \<goal\>, do \<action\>.” For example:

> To check the state of available VMs, run `onevm show`.

If an instruction refers to elements that are one within the other, try to write it so that it references first the major, then the minor elements. For example:

> On the Front-end, check that the NFS share containing the datastores is mounted, by running the `df` command. 
The above sentence goes from the *Front-end* to *NFS share* to the *datastore* within the share.

[Back to top](#style-guide-for-technical-documentation)

### Gender-neutral Writing

To avoid problems with pronouns and gender, the best method is to avoid using pronouns altogether. For example, using the imperative mood described above eliminates the problem of gender-neutral writing. For example:

| Indicative mood | Imperative mood |
| :---- | :---- |
| The user will need his or her password to access the system. | You will need your password to access the system. |

Another method is to use plural nouns, e.g.:

> Users will need their passwords to access the system.

#### Short Explanation

A noun is the name of a person, thing, action, place, or idea. For example, *user* or *system*. A pronoun is a word that replaces the noun (*he*, *she*, *they* or *it*), or to indicate possession (*his*, *her*, *their*). In English, problems with gender neutrality derive from the facts that:

* Sentences must always possess a subject, which is a *noun* or *pronoun*
* There is no *singular* gender-neutral *pronoun*

There are several methods to use gender-inclusive pronouns, but all of these present various difficulties, which means that they are either semantically incorrect (such as using the gender-neutral plural *their* to refer to a singular subject) or that they produce awkward sentences or annoy some readers (such as using "he or she").

For these reasons the recommended approach is to try to avoid this situation altogether, by using a plural subject (i.e. *users* instead of *the user*), or imperative mood.