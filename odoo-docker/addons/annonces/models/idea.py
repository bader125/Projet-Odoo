from odoo import models, fields, api  # type: ignore

class InternalAnnouncement(models.Model):
    _name = "internal.announcement"
    _description = "Annonce Interne"
    _order = "publication_date desc, priority desc, id desc"

    name = fields.Char(string="Référence", readonly=True, default=lambda self: 'New')
    title = fields.Char(string="Titre", required=True, help="Titre de l'annonce")
    content = fields.Html(string="Contenu", required=True, help="Contenu détaillé de l'annonce")
    
    # Auteur et dates
    author_id = fields.Many2one('res.users', string="Auteur", required=True, default=lambda self: self.env.user, readonly=True)
    creation_date = fields.Datetime(string="Date de création", default=fields.Datetime.now, readonly=True)
    publication_date = fields.Datetime(string="Date de publication", help="Date à laquelle l'annonce sera publiée")
    expiration_date = fields.Datetime(string="Date d'expiration", help="Date à laquelle l'annonce expirera (optionnel)")
    
    # Catégorie et priorité
    category = fields.Selection([
        ('information', 'Information'),
        ('event', 'Événement'),
        ('urgent', 'Urgent'),
        ('policy', 'Politique'),
        ('training', 'Formation'),
        ('general', 'Général'),
        ('other', 'Autre')
    ], string="Catégorie", required=True, default='general')
    
    priority = fields.Selection([
        ('0', 'Normale'),
        ('1', 'Importante'),
        ('2', 'Urgente')
    ], string="Priorité", default='0', required=True)
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('published', 'Publiée'),
        ('archived', 'Archivée')
    ], string="Statut", default='draft', required=True)
    
    # Pièces jointes et visibilité
    attachment_ids = fields.Many2many('ir.attachment', string="Pièces jointes", help="Joindre des documents si nécessaire")
    is_active = fields.Boolean(string="Active", default=True, help="Désactiver pour masquer l'annonce sans l'archiver")
    
    # Compteurs
    view_count = fields.Integer(string="Nombre de vues", default=0, readonly=True)
    
    # Champ calculé pour vérifier si l'annonce est expirée
    is_expired = fields.Boolean(string="Expirée", compute="_compute_is_expired", store=True)
    
    @api.depends('expiration_date', 'state')
    def _compute_is_expired(self):
        for record in self:
            if record.expiration_date and record.state == 'published':
                record.is_expired = fields.Datetime.now() > record.expiration_date
            else:
                record.is_expired = False
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('internal.announcement') or 'New'
        if not vals.get('publication_date'):
            vals['publication_date'] = fields.Datetime.now()
        return super(InternalAnnouncement, self).create(vals)
    
    def action_publish(self):
        """Publie l'annonce"""
        self.write({
            'state': 'published',
            'publication_date': fields.Datetime.now() if not self.publication_date else self.publication_date,
            'is_active': True
        })
    
    def action_archive(self):
        """Archive l'annonce"""
        self.write({
            'state': 'archived',
            'is_active': False
        })
    
    def action_reset_to_draft(self):
        """Remet l'annonce en brouillon"""
        self.write({'state': 'draft'})
    
    def action_increment_view(self):
        """Incrémente le compteur de vues"""
        self.write({'view_count': self.view_count + 1})
    
    @api.model
    def get_active_announcements(self):
        """Retourne les annonces actives et non expirées"""
        now = fields.Datetime.now()
        return self.search([
            ('state', '=', 'published'),
            ('is_active', '=', True),
            '|',
            ('expiration_date', '=', False),
            ('expiration_date', '>', now)
        ], order='priority desc, publication_date desc')