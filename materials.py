class Material:
    def __init__(self, diffuse=(1.0, 1.0, 1.0), specular=(0.0, 0.0, 0.0), 
                 shininess=0.0, alpha=1.0, emission=(0.0, 0.0, 0.0), 
                 roughness=1.0, name="Material"):
        self.diffuse = list(diffuse)
        self.specular = list(specular)
        self.shininess = shininess
        self.alpha = alpha
        self.emission = list(emission)
        self.roughness = roughness
        self.name = name
        
        # Save original diffuse for mirror walls
        self.original_diffuse = list(diffuse)
    
    def make_mirror(self):
        """Convert material to mirror-like"""
        self.specular = [0.8, 0.8, 0.8]
        self.shininess = 120.0
        self.roughness = 0.1
    
    def make_transparent(self, alpha=0.5):
        """Make material transparent"""
        self.alpha = alpha
    
    def reset(self):
        """Reset material to default"""
        self.specular = [0.0, 0.0, 0.0]
        self.shininess = 0.0
        self.alpha = 1.0
        self.roughness = 1.0